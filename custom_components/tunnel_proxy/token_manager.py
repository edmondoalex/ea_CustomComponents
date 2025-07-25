import json
import os
import secrets
import logging
import requests

_LOGGER = logging.getLogger(__name__)

def get_existing_token(token_path, name, url):
    if not os.path.exists(token_path):
        _LOGGER.debug(f"File token {token_path} non trovato.")
        return None
    try:
        with open(token_path, "r") as f:
            tokens = json.load(f)
        for item in tokens:
            if item["name"] == name and item["url"] == url:
                _LOGGER.debug(f"Token trovato per name={name} url={url}.")
                return item["token"]
    except Exception as e:
        _LOGGER.warning(f"Errore leggendo file token: {e}")
    return None

def save_token(token_path, name, url, token, device_id):
    tokens = []
    try:
        if os.path.exists(token_path):
            with open(token_path, "r") as f:
                try:
                    tokens = json.load(f)
                    _LOGGER.debug(f"Token file letto, tokens: {tokens}")
                except json.JSONDecodeError:
                    _LOGGER.warning(f"File token vuoto o corrotto, resetto lista tokens.")
                    tokens = []
        for item in tokens:
            if item["name"] == name and item["url"] == url:
                _LOGGER.debug(f"Token già presente per {name} e {url}, non salvo nuovamente.")
                return
        tokens.append({
            "name": name,
            "url": url,
            "id": device_id,
            "token": token
        })
        with open(token_path, "w") as f:
            json.dump(tokens, f, indent=2)
        _LOGGER.info(f"Token salvato correttamente per {name} e {url}.")
    except Exception as e:
        _LOGGER.error(f"Errore durante salvataggio token: {e}")


def send_token(url, name, token, device_id):
    try:
        payload = {"name": name, "token": token, "id": device_id}
        headers = {"Content-Type": "application/json"}
        full_url = f"{url}/proxy/register"
        _LOGGER.info(f"Invio token a {full_url} con payload: {payload}")
        response = requests.post(full_url, json=payload, headers=headers, timeout=5)

        if response.status_code == 200:
            _LOGGER.info(f"Token inviato correttamente: {response.status_code} - {response.text}")
        else:
            _LOGGER.error(f"Errore dal server {url}: {response.status_code} - {response.text}")
    except Exception as e:
        _LOGGER.error(f"Errore durante invio token a {url}: {e}")

async def async_generate_token_and_notify(hass, name, url, device_id):
    token_path = hass.config.path("server_tokens.json")
    existing_token = await hass.async_add_executor_job(get_existing_token, token_path, name, url)
    if existing_token:
        _LOGGER.debug("Token già esistente, non rigenerato né inviato di nuovo.")
        return

    token = secrets.token_urlsafe(32)
    _LOGGER.info(f"Generazione nuovo token per name={name} url={url}")
    await hass.async_add_executor_job(save_token, token_path, name, url, token, device_id)
    await hass.async_add_executor_job(send_token, url, name, token, device_id)
