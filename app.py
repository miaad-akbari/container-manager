from flask import Flask, render_template, request, jsonify
import docker

app = Flask(__name__)
docker_client = docker.from_env()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_container', methods=['POST'])
def create_container():
    # Get form data
    data = request.form

    # Basic info
    image_name = data.get('image_name')
    if not image_name:
        return jsonify({'error': 'Image name is required!'}), 400

    container_name = data.get('container_name', None)

    # Ports (e.g., "8080:80")
    ports = {}
    port_mapping = data.get('port_mapping', '')
    if port_mapping:
        try:
            host_port, container_port = port_mapping.split(':')
            ports[container_port] = host_port
        except ValueError:
            return jsonify({'error': 'Invalid port mapping format! Use "host_port:container_port".'}), 400

    # Environment variables (e.g., "KEY1=VALUE1,KEY2=VALUE2")
    environment = {}
    env_vars = data.get('environment', '')
    if env_vars:
        for env_pair in env_vars.split(','):
            if '=' in env_pair:
                key, value = env_pair.split('=')
                environment[key] = value

    # Volumes (e.g., "/host/path:/container/path")
    volumes = {}
    volume_mapping = data.get('volume_mapping', '')
    if volume_mapping:
        try:
            host_path, container_path = volume_mapping.split(':')
            volumes[host_path] = {'bind': container_path, 'mode': 'rw'}
        except ValueError:
            return jsonify({'error': 'Invalid volume mapping format! Use "/host/path:/container/path".'}), 400

    # Network (e.g., "bridge")
    network = data.get('network', 'bridge')

    try:
        # Create container
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
            'container_name': container.name,
            'ports': ports  # Return port mapping for access URL
        }), 201
    except docker.errors.ImageNotFound:
        return jsonify({'error': f'Image "{image_name}" not found on Docker Hub!'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/list_containers', methods=['GET'])
def list_containers():
    try:
        containers = docker_client.containers.list(all=True)
        container_list = []
        for container in containers:
            container_list.append({
                'id': container.id,
                'name': container.name,
                'status': container.status
            })
        return jsonify({'containers': container_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stop_container', methods=['POST'])
def stop_container():
    container_id = request.form.get('container_id')
    if not container_id:
        return jsonify({'error': 'Container ID is required!'}), 400

    try:
        container = docker_client.containers.get(container_id)
        container.stop()
        return jsonify({'message': f'Container {container_id} stopped successfully!'}), 200
    except docker.errors.NotFound:
        return jsonify({'error': f'Container {container_id} not found!'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_container', methods=['POST'])
def delete_container():
    container_id = request.form.get('container_id')
    if not container_id:
        return jsonify({'error': 'Container ID is required!'}), 400

    try:
        container = docker_client.containers.get(container_id)
        container.remove(force=True)
        return jsonify({'message': f'Container {container_id} deleted successfully!'}), 200
    except docker.errors.NotFound:
        return jsonify({'error': f'Container {container_id} not found!'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)