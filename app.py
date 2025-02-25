from flask import Flask, jsonify, request, render_template
from proxmoxer import ProxmoxAPI
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)  # Erlaubt CORS-Anfragen

# Konfiguration: Passe diese Parameter an Deine Umgebung an
PROXMOX_HOST = '192.168.XXX.XXX'
PROXMOX_NODE = 'pve'
DEFAULT_VM_ID = 100  # Fallback-VMID, falls keine Auswahl erfolgt

# API-Zugangsdaten
API_USER = 'USERNAME@pam'
API_TOKEN_NAME = 'API_TOKEN_NAME'
API_TOKEN_SECRET = 'API_TOKEN_SECRET'

# Erstelle eine ProxmoxAPI-Instanz (SSL-Überprüfung ggf. deaktivieren, falls nötig)
proxmox = ProxmoxAPI(PROXMOX_HOST,
                     user=API_USER,
                     token_name=API_TOKEN_NAME,
                     token_value=API_TOKEN_SECRET,
                     verify_ssl=False)

@app.route('/')
def index():
    try:
        # Abrufen aller VMs auf dem spezifizierten Node
        vm_list = proxmox.nodes(PROXMOX_NODE).qemu.get()
    except Exception as e:
        vm_list = []
    return render_template('index.html', vm_list=vm_list)

@app.route('/start_vm', methods=['POST'])
def start_vm():
    try:
        data = request.get_json()
        # Hole die ausgewählte VMID aus dem Request; wenn nicht vorhanden, verwende DEFAULT_VM_ID
        vmid = int(data.get('vmid', DEFAULT_VM_ID))
        # Flag, ob technische Details angezeigt werden sollen
        show_details = data.get('show_details', False)
        # Optional: Unterscheidung, ob die Anfrage von Home Assistant kommt
        source = data.get('source', 'web')  # 'ha' oder 'web'
        
        # Sende den Befehl zum Starten der VM
        response = proxmox.nodes(PROXMOX_NODE).qemu(vmid).status.start.post()
        
        # Human-readable Message; optional: anhand der VMID auch den VM-Namen anzeigen
        human_message = f"Die VM mit der ID {vmid} wurde erfolgreich gestartet."
        
        result = {
            'human_message': human_message
        }
        # Technische Details nur anhängen, wenn gewünscht
        if show_details:
            formatted_response = json.dumps(response, indent=2, ensure_ascii=False)
            result['technical_details'] = formatted_response
        
        # Falls die Anfrage von Home Assistant kommt, könnte man hier noch weitere Anpassungen vornehmen.
        if source == 'ha':
            # Beispielsweise nur die menschenlesbare Nachricht zurückgeben.
            result = {'human_message': human_message}
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
