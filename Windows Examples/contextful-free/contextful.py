"""
Microservice for a context-aware ChatGPT assistant.

The following program reads in a collection of documents,
embeds each document using the OpenAI document embedding model,
then builds an index for fast retrieval of documents relevant to a question,
effectively replacing a vector database.

The program then starts a REST API endpoint serving queries about programming in Pathway.

Each query text is first turned into a vector using OpenAI embedding service,
then relevant documentation pages are found using a Nearest Neighbor index computed
for documents in the corpus. A prompt is built from the relevant documentation pages
and sent to the OpenAI chat service for processing.

Please check the README.md in this directory for how-to-run instructions.
"""

import os

import dotenv
import pathway as pw
from pathway.stdlib.ml.index import KNNIndex
from pathway.xpacks.llm.embedders import SentenceTransformerEmbedder
from pathway.xpacks.llm.llms import LiteLLMChat, prompt_chat_single_qa

dotenv.load_dotenv()
os.environ['GROQ_API_KEY'] = "FIRST PUT YOUR GROQ API KEY HERE"

class DocumentInputSchema(pw.Schema):
    doc: str


class QueryInputSchema(pw.Schema):
    query: str
    user: str


def run(
    *,
    data_dir: str = os.environ.get("PATHWAY_DATA_DIR", "_data"),
    host: str = os.environ.get("PATHWAY_REST_CONNECTOR_HOST", "0.0.0.0"),
    port: int = int(os.environ.get("PATHWAY_REST_CONNECTOR_PORT", "8080")),
    embedder_locator: str = "Alibaba-NLP/gte-base-en-v1.5",
    embedding_dimension: int = 768,
    model_locator: str = "groq/llama3-70b-8192", # EXPERIMENT WITH DIFFERENT MODELS
    max_tokens: int = 60, # TRY PLUGGING INTO LITELLM AND EXPERIMENT WITH DIFFERENT VALUES
    temperature: float = 0.0, # TRY PLUGGING INTO LITELLM AND EXPERIMENT WITH DIFFERENT VALUES
    **kwargs,
):
    # embedder = OpenAIEmbedder(
    #     api_key=api_key,
    #     model=embedder_locator,
    #     retry_strategy=pw.udfs.FixedDelayRetryStrategy(),
    #     cache_strategy=pw.udfs.DefaultCache(),
    # )

    embedder = SentenceTransformerEmbedder(
        model=embedder_locator,
        trust_remote_code=True
    )

    documents = pw.io.jsonlines.read(
        data_dir,
        schema=DocumentInputSchema,
        mode="streaming",
        autocommit_duration_ms=50,
    )

    enriched_documents = documents + documents.select(vector=embedder(pw.this.doc))

    index = KNNIndex(
        enriched_documents.vector, enriched_documents, n_dimensions=embedding_dimension
    )

    query, response_writer = pw.io.http.rest_connector(
        host=host,
        port=port,
        schema=QueryInputSchema,
        autocommit_duration_ms=50,
        delete_completed_queries=True,
    )

    query += query.select(vector=embedder(pw.this.query))

    query_context = query + index.get_nearest_items(
        query.vector, k=3, collapse_rows=True
    ).select(documents_list=pw.this.doc)

    @pw.udf
    def build_prompt(documents, query):
        docs_str = "\n".join(documents)
        prompt = f"Given the following documents : \n {docs_str} \nanswer this query: {query}"
        return prompt

    prompt = query_context.select(
        prompt=build_prompt(pw.this.documents_list, pw.this.query)
    )

    # model = OpenAIChat(
    #     api_key=api_key,
    #     model=model_locator,
    #     temperature=temperature,
    #     max_tokens=max_tokens,
    #     retry_strategy=pw.udfs.FixedDelayRetryStrategy(),
    #     cache_strategy=pw.udfs.DefaultCache(),
    # )

    model = LiteLLMChat(
        model = model_locator
    )

    responses = prompt.select(
        query_id=pw.this.id, result=model(prompt_chat_single_qa(pw.this.prompt))
    )

    response_writer(responses)

    pw.run()


if __name__ == "__main__":
    run()