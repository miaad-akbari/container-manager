from flask import Flask, render_template, request, jsonify
import docker

app = Flask(__name__)
docker_client = docker.from_env()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_container', methods=['POST'])
def create_container():
       
    data = request.form

      
    image_name = data.get('image_name')
    container_name = data.get('container_name', None)

    
    ports = {}
    port_mapping = data.get('port_mapping', '')
    if port_mapping:
        host_port, container_port = port_mapping.split(':')
        ports[container_port] = host_port

    
    environment = {}
    env_vars = data.get('environment', '')
    if env_vars:
        for env_pair in env_vars.split(','):
            if '=' in env_pair:
                key, value = env_pair.split('=')
                environment[key] = value

   
    volumes = {}
    volume_mapping = data.get('volume_mapping', '')
    if volume_mapping:
        host_path, container_path = volume_mapping.split(':')
        volumes[host_path] = {'bind': container_path, 'mode': 'rw'}

   
    network = data.get('network', 'bridge')

    try:
         
        container = docker_client.containers.run(
            image=image_name,
            name=container_name,
            ports=ports,
            environment=environment,
            volumes=volumes,
            network=network,
            detach=True
        )
        return jsonify({
            'message': 'Container created successfully!',
            'container_id': container.id,
            'container_name': container.name
        }), 201
    except docker.errors.ImageNotFound:
        return jsonify({'error': f'Image "{image_name}" not found on Docker Hub!'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)