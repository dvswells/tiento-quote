"""
Visualization utilities for Tiento Quote v0.1.

Handles STEP to STL conversion and Three.js viewer generation for 3D visualization.
"""
import os
from typing import Tuple
import cadquery as cq
from modules.domain import PartFeatures


def compute_adaptive_deflection(features: PartFeatures) -> Tuple[float, float]:
    """
    Compute adaptive deflection parameters based on part size.

    Uses 0.1% of the largest bounding box dimension for linear deflection
    and 0.5 degrees for angular deflection (per spec).

    Args:
        features: Part features with bounding box dimensions

    Returns:
        Tuple of (linear_deflection, angular_deflection)
        - linear_deflection: 0.1% of max dimension (mm)
        - angular_deflection: 0.5 degrees

    Example:
        >>> features = PartFeatures(bounding_box_x=100, bounding_box_y=200, bounding_box_z=150)
        >>> linear, angular = compute_adaptive_deflection(features)
        >>> # linear = 200 * 0.001 = 0.2 (0.1% of 200mm)
        >>> # angular = 0.5 (degrees)
    """
    # Find maximum dimension
    max_dimension = max(
        features.bounding_box_x,
        features.bounding_box_y,
        features.bounding_box_z
    )

    # Linear deflection: 0.1% of largest dimension
    linear_deflection = max_dimension * 0.001

    # Angular deflection: fixed at 0.5 degrees
    angular_deflection = 0.5

    return linear_deflection, angular_deflection


def step_to_stl(
    step_path: str,
    stl_path: str,
    linear_deflection: float,
    angular_deflection: float
) -> None:
    """
    Convert STEP file to STL format for visualization.

    Uses cadquery to load STEP geometry and export as ASCII STL with
    specified mesh resolution parameters.

    Args:
        step_path: Path to input STEP file
        stl_path: Path where STL file should be saved
        linear_deflection: Maximum linear deviation from surface (mm)
        angular_deflection: Maximum angular deviation from surface (degrees)

    Raises:
        Exception: If STEP file cannot be loaded or STL export fails

    Example:
        >>> step_to_stl("part.step", "part.stl", 0.1, 0.5)
        >>> # Creates ASCII STL file with adaptive mesh resolution
    """
    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(os.path.abspath(stl_path)), exist_ok=True)

    # Load STEP file
    try:
        result = cq.importers.importStep(step_path)
    except Exception as e:
        raise Exception(f"Failed to load STEP file: {step_path}. Error: {str(e)}")

    # Ensure result is a Workplane
    if not isinstance(result, cq.Workplane):
        result = cq.Workplane("XY").add(result)

    # Export to STL with specified deflection parameters
    # exportStl() uses linearDeflection and angularDeflection for mesh resolution
    try:
        cq.exporters.export(
            result,
            stl_path,
            exportType=cq.exporters.ExportTypes.STL,
            tolerance=linear_deflection,
            angularTolerance=angular_deflection
        )
    except Exception as e:
        raise Exception(f"Failed to export STL file: {stl_path}. Error: {str(e)}")


def build_threejs_viewer_html(stl_bytes_or_url: str) -> str:
    """
    Build self-contained HTML for Three.js 3D viewer.

    Creates a complete HTML page with Three.js viewer that can load and display
    STL files. Uses CDN-hosted Three.js, STLLoader, and OrbitControls for
    interactive 3D visualization.

    Args:
        stl_bytes_or_url: URL to STL file, data URL (base64), or file path

    Returns:
        Self-contained HTML string ready for rendering

    Example:
        >>> html = build_threejs_viewer_html("model.stl")
        >>> # Can be rendered in Streamlit with st.components.v1.html(html)
    """
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>3D Model Viewer</title>
    <style>
        body {{
            margin: 0;
            overflow: hidden;
            font-family: Arial, sans-serif;
        }}
        #container {{
            width: 100%;
            height: 600px;
        }}
    </style>
</head>
<body>
    <div id="container"></div>

    <!-- Three.js from CDN -->
    <script src="https://cdn.jsdelivr.net/npm/three@0.158.0/build/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.158.0/examples/js/loaders/STLLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.158.0/examples/js/controls/OrbitControls.js"></script>

    <script>
        // Set up scene, camera, and renderer
        const container = document.getElementById('container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf0f0f0);

        const camera = new THREE.PerspectiveCamera(
            75,
            container.clientWidth / container.clientHeight,
            0.1,
            10000
        );

        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(container.clientWidth, container.clientHeight);
        container.appendChild(renderer.domElement);

        // Add lighting
        const ambientLight = new THREE.AmbientLight(0x404040, 2);
        scene.add(ambientLight);

        const directionalLight1 = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight1.position.set(1, 1, 1);
        scene.add(directionalLight1);

        const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.5);
        directionalLight2.position.set(-1, -1, -1);
        scene.add(directionalLight2);

        // Add OrbitControls for camera interaction
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.screenSpacePanning = false;
        controls.minDistance = 1;
        controls.maxDistance = 5000;

        // Load STL file
        const loader = new THREE.STLLoader();
        loader.load(
            '{stl_bytes_or_url}',
            function (geometry) {{
                const material = new THREE.MeshPhongMaterial({{
                    color: 0x5555ff,
                    specular: 0x111111,
                    shininess: 200
                }});

                const mesh = new THREE.Mesh(geometry, material);

                // Center the geometry
                geometry.computeBoundingBox();
                const boundingBox = geometry.boundingBox;
                const center = new THREE.Vector3();
                boundingBox.getCenter(center);
                mesh.position.sub(center);

                scene.add(mesh);

                // Position camera to view the model
                const size = new THREE.Vector3();
                boundingBox.getSize(size);
                const maxDim = Math.max(size.x, size.y, size.z);
                const fov = camera.fov * (Math.PI / 180);
                const cameraDistance = Math.abs(maxDim / Math.sin(fov / 2)) * 1.5;

                camera.position.set(cameraDistance, cameraDistance, cameraDistance);
                camera.lookAt(0, 0, 0);
                controls.update();
            }},
            function (xhr) {{
                // Progress callback
                console.log((xhr.loaded / xhr.total * 100) + '% loaded');
            }},
            function (error) {{
                console.error('Error loading STL:', error);
            }}
        );

        // Animation loop
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}

        animate();

        // Handle window resize
        window.addEventListener('resize', function() {{
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        }});
    </script>
</body>
</html>
"""
    return html
