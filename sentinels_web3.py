import requests
import json
from web3 import Web3
from datetime import datetime

API_KEY = ''
API_Secret = ''
INFURA_URL = ""
CONTRACT_ADDRESS = ""
WALLET_ADDRESS = ""
PRIVATE_KEY = ""
ABI_PATH = "contract_abi.json"

w3 = Web3(Web3.HTTPProvider(INFURA_URL))
contract_abi = json.load(open(ABI_PATH))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

def upload_to_ipfs(json_data: dict) -> str:
    url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    headers = {
        "Content-Type": "application/json",
        "pinata_api_key": API_KEY,
        "pinata_secret_api_key": API_Secret
    }
    response = requests.post(url, headers=headers, json=json_data)
    if response.status_code != 200:
        raise Exception(f"Pinata upload failed: {response.text}")
    cid = response.json()['IpfsHash']
    return f"ipfs://{cid}"

def get_public_ip():
    return requests.get("https://api64.ipify.org?format=json").json()['ip']

def upload_event_and_reward(data, important):
    data['ip'] = get_public_ip()
    ipfs_hash = upload_to_ipfs(data)
    nonce = w3.eth.get_transaction_count(WALLET_ADDRESS, 'pending')
    tx = contract.functions.logEventAndMint(
        'Sentinels-Node-1',
        ipfs_hash,
        important
    ).build_transaction({
        'gas': 250000,
        'gasPrice': w3.to_wei('10', 'gwei'),
        'nonce': nonce
    })
    nonce += 1
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Transaction sent: {tx_hash.hex()}")
    return tx_hash.hex()
