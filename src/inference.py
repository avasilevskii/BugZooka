import logging

import requests
from src.constants import GENERIC, INFERENCE_TOP_P, INFERENCE_FREQUENCY_PENALTY, INFERENCE_TEMPERATURE, INFERENCE_MAX_TOKENS

logger = logging.getLogger(__name__)


def ask_inference_api(
        messages,
        url,
        api_token,
        model,
        top_p=INFERENCE_TOP_P,
        frequency_penalty=INFERENCE_FREQUENCY_PENALTY,
        temperature=INFERENCE_TEMPERATURE,
        max_tokens=INFERENCE_MAX_TOKENS,
        organization=None,
        cache=None,
        verbose=False):
    """
    Sends a request to the inference API with configurable parameters.

    :param messages: List of message dictionaries with 'role' and 'content'
    :param url: Inference API base URL
    :param api_token: API authentication token
    :param model: Model to use for inference (default: gpt-4)
    :param top_p: Nucleus sampling probability (default: 0.95)
    :param frequency_penalty: Penalty for frequent tokens (default: 1.03)
    :param temperature: Controls randomness (default: 0.01)
    :param max_tokens: Maximum tokens to generate (default: 512)
    :param organization: Optional organization ID
    :param cache: Optional cache settings
    :param verbose: If True, prints additional logs
    :return: AI response text or an error message
    """
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "verbose": True,
    }

    # Add optional parameters if they are provided
    if organization:
        payload["organization"] = organization
    if cache is not None:
        payload["cache"] = cache

    if verbose:
        logger.info("Sending request with payload:", payload)

    try:
        response = requests.post(
            f"{url}/v1/chat/completions", json=payload, headers=headers
        )
        response.raise_for_status()
        return (
            response.json()
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content", "No content returned.")
        )

    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"


def analyze_log(product: str, product_config: dict, error_summary: str) -> str:
    """
    Analyzes log summaries (generic or product-specific) using config-driven prompting.

    :param product: Product name or "GENERIC"
    :param product_config: Config dict with prompt, endpoint, token, and model info
    :param error_summary: Error summary text to analyze
    :return: Analysis result
    """
    try:
        prompt_config = product_config["prompt"][product]
        try:
            formatted_content = prompt_config["user"].format(
                error_summary=error_summary
            )
        except KeyError:
            formatted_content = prompt_config["user"].format(
                summary=error_summary)

        messages = [
            {"role": "system", "content": prompt_config["system"]},
            {"role": "user", "content": formatted_content},
            {"role": "assistant", "content": prompt_config["assistant"]},
        ]

        return ask_inference_api(
            messages=messages,
            url=product_config["endpoint"][product],
            api_token=product_config["token"][product],
            model=product_config["model"][product],
            max_tokens=INFERENCE_MAX_TOKENS,
        )

    except Exception as e:
        logger.error(f"Error analyzing {product} log: {e}")
        return f"Error analyzing log: {e}"


def analyze_product_log(product, product_config, error_summary):
    """
    Analyzes product-specific log summaries.

    :param product: product name
    :param product_config: product configuration
    :param error_summary: error summary text to analyze
    :return: analysis result
    """
    return analyze_log(product, product_config, error_summary)


def analyze_generic_log(product_config, error_summary):
    """
    Analyzes generic log summaries.

    :param product_config: product configuration
    :param error_summary: error summary text to analyze
    :return: analysis result
    """
    return analyze_log(GENERIC, product_config, error_summary)
