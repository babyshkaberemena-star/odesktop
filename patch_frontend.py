import re
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Configuration
# Path relative to repos/odesktop root
OD_PATH = "Telegram/SourceFiles/mtproto/mtproto_dc_options.cpp"
BACKEND_IP = "127.0.0.1"
BACKEND_PORT = 4430 # MTProto Port

def generate_rsa_keys():
    print("Generating new RSA Key Pair for God Mode...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem.decode('utf-8'), public_pem.decode('utf-8')

def patch_client(public_key_pem):
    if not os.path.exists(OD_PATH):
        print(f"Error: Could not find {OD_PATH}")
        print("Current Directory:", os.getcwd())
        return

    with open(OD_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Patch Built-in DCs
    # We want to replace the kBuiltInDcs array content
    # Pattern matches the array definition up to the closing brace
    dc_pattern = r"const BuiltInDc kBuiltInDcs\[\] = \{.*?\};"
    
    # New DC config for Localhost
    new_dc_config = f"""const BuiltInDc kBuiltInDcs[] = {{
	{{ 1, "{BACKEND_IP}", {BACKEND_PORT}, 0, "{BACKEND_IP}" }},
	{{ 2, "{BACKEND_IP}", {BACKEND_PORT}, 0, "{BACKEND_IP}" }},
	{{ 3, "{BACKEND_IP}", {BACKEND_PORT}, 0, "{BACKEND_IP}" }} 
}};"""
    
    # Use dotall to match newlines
    content = re.sub(dc_pattern, new_dc_config, content, flags=re.DOTALL)
    
    # 2. Patch Public Keys
    # We replace both Test and Prod keys to be sure
    key_pattern = r"const char \*kPublicRSAKeys\[\] = \{.*?\};"
    
    # Format PEM for C++ string literal (newlines become \n inside string)
    pem_clean = public_key_pem.strip()
    # We need to format it exactly as the C++ file expects: "..." \n "..."
    # But simpler is just one long string with \n literal
    
    cpp_key_string = '"{}"'.format(pem_clean.replace('\n', '\\n\\\n'))
    
    new_key_config = f"""const char *kPublicRSAKeys[] = {{ \\
{cpp_key_string} }};"""

    content = re.sub(key_pattern, new_key_config, content, flags=re.DOTALL)
    
    # Also patch Test Keys just in case
    test_key_pattern = r"const char \*kTestPublicRSAKeys\[\] = \{.*?\};"
    new_test_key_config = f"""const char *kTestPublicRSAKeys[] = {{ \\
{cpp_key_string} }};"""
    content = re.sub(test_key_pattern, new_test_key_config, content, flags=re.DOTALL)

    with open(OD_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Successfully patched {OD_PATH}")

def main():
    private_pem, public_pem = generate_rsa_keys()
    
    # Save Private Key for Backend
    # We save it two levels up so it is in tggg root
    with open("../../server_private.pem", "w") as f:
        f.write(private_pem)
    print("Saved server_private.pem to root workspace")
    
    # Also copy to docker folder if possible
    try:
        with open("../../repos/opengram/docker/compose/rsa_key.pem", "w") as f:
            f.write(private_pem)
        print("Updated Docker key automatically.")
    except:
        print("Could not auto-update Docker key, please copy server_private.pem manually.")

    patch_client(public_pem)

if __name__ == "__main__":
    main()
