import paramiko
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from secret import hosts, ssh_key_path, porta, usuario  # Importa as configurações do arquivo secret.py

# Configuração do logger
logging.basicConfig(
    filename="cadastro_rede.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Função para conectar e cadastrar as redes no host remoto
def cadastrar_rede_em_host(host, porta, usuario, ssh_key_path, redes, codigo, threshold):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        ssh.connect(host, port=porta, username=usuario, key_filename=ssh_key_path)

        for rede in redes:
            comando = f"sudo /usr/local/bin/cadastra_rede_sp2 {rede} {codigo} {threshold}"
            stdin, stdout, stderr = ssh.exec_command(comando)
            stdout.channel.recv_exit_status()  # Aguarda a execução do comando
            
            output = stdout.read().decode()
            error = stderr.read().decode()
            logging.info(f"[{host}] {output}")
            logging.error(f"[{host}] {error}") if error else None
        
        ssh.close()
        return f"Cadastro concluído para o host {host}."
    except Exception as e:
        return f"Erro ao conectar-se ao host {host}: {e}"

def main():
    if len(sys.argv) < 4:
        print("Uso: python3 cadastra_rede.py <arquivo_prefixos.txt> <codigo> <threshold>")
        sys.exit(1)
    
    # Lê o arquivo de prefixos
    arquivo_prefixos = sys.argv[1]
    try:
        with open(arquivo_prefixos, 'r') as f:
            prefixos = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Erro: O arquivo {arquivo_prefixos} não foi encontrado.")
        sys.exit(1)

    codigo = sys.argv[2]
    threshold = sys.argv[3]
    
    # Exibe as redes e confirma a operação
    print(f"\nCOD: {codigo}\nThreshold: {threshold}\n\nRedes:")
    for prefixo in prefixos:
        print(prefixo)

    confirmacao = input("\nDeseja prosseguir com o cadastro das seguintes redes? (s/n): ")
    if confirmacao.lower() != 's':
        print("Cancelando operação.")
        sys.exit()

    redes = prefixos
    print("Iniciando cadastro de prefixos...")
    with ThreadPoolExecutor(max_workers=len(hosts)) as executor:
        # Cria uma lista de futuros para cada tarefa
        futuros = {
            executor.submit(cadastrar_rede_em_host, host, porta, usuario, ssh_key_path, redes, codigo, threshold): host
            for host in hosts
        }
        
        # Processa os resultados conforme os threads terminam
        for futuro in as_completed(futuros):
            host = futuros[futuro]
            try:
                resultado = futuro.result()
                print(f"Resultado para {host}: {resultado}")
            except Exception as e:
                print(f"Erro ao processar {host}: {e}")

if __name__ == "__main__":
    main()