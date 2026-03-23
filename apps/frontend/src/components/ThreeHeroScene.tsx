'use client';

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface ThreeHeroSceneProps {
  className?: string;
  density?: 'hero' | 'ambient';
}

export const ThreeHeroScene = ({ className, density = 'hero' }: ThreeHeroSceneProps) => {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const hasRenderableSize = () => mount.clientWidth > 1 && mount.clientHeight > 1;
    const getSafeSize = () => ({
      width: Math.max(mount.clientWidth, 1),
      height: Math.max(mount.clientHeight, 1),
    });

    if (!hasRenderableSize()) {
      return;
    }

    type Cleanup = () => void;

    const initWebGLFallback = (): Cleanup => {
      const scene = new THREE.Scene();
      scene.fog = new THREE.Fog('#090315', 5, 14);

      const { width, height } = getSafeSize();

      const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
      camera.position.set(0, density === 'hero' ? 1.05 : 0.8, density === 'hero' ? 8.3 : 6.8);

      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setSize(width, height);
      mount.appendChild(renderer.domElement);

      const galaxyGroup = new THREE.Group();

      const particleCount = density === 'hero' ? 15000 : 4800;
      const galaxyRadius = density === 'hero' ? 5.9 : 4.4;
      const branches = 3;
      const spin = density === 'hero' ? 1.2 : 1.0;
      const randomness = density === 'hero' ? 0.45 : 0.35;
      const randomnessPower = 3;

      const positions = new Float32Array(particleCount * 3);
      const colors = new Float32Array(particleCount * 3);

      const colorInside = new THREE.Color('#ffa575');
      const colorOutside = new THREE.Color('#311599');

      for (let i = 0; i < particleCount; i += 1) {
        const i3 = i * 3;
        const radiusSample = Math.pow(Math.random(), 1.4) * galaxyRadius;
        const branchAngle = ((i % branches) / branches) * Math.PI * 2;
        const spinAngle = radiusSample * spin;

        const randomX =
          Math.pow(Math.random(), randomnessPower) *
          (Math.random() < 0.5 ? 1 : -1) *
          randomness *
          radiusSample;
        const randomY =
          Math.pow(Math.random(), randomnessPower) *
          (Math.random() < 0.5 ? 1 : -1) *
          randomness *
          0.35 *
          radiusSample;
        const randomZ =
          Math.pow(Math.random(), randomnessPower) *
          (Math.random() < 0.5 ? 1 : -1) *
          randomness *
          radiusSample;

        positions[i3] = Math.cos(branchAngle + spinAngle) * radiusSample + randomX;
        positions[i3 + 1] = randomY;
        positions[i3 + 2] = Math.sin(branchAngle + spinAngle) * radiusSample + randomZ;

        const mixedColor = colorInside.clone();
        mixedColor.lerp(colorOutside, radiusSample / galaxyRadius);

        colors[i3] = mixedColor.r;
        colors[i3 + 1] = mixedColor.g;
        colors[i3 + 2] = mixedColor.b;
      }

      const galaxyGeometry = new THREE.BufferGeometry();
      galaxyGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      galaxyGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

      const galaxyMaterial = new THREE.PointsMaterial({
        size: density === 'hero' ? 0.038 : 0.026,
        sizeAttenuation: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        vertexColors: true,
        transparent: true,
        opacity: density === 'hero' ? 0.95 : 0.82,
      });

      const galaxyPoints = new THREE.Points(galaxyGeometry, galaxyMaterial);
      galaxyPoints.rotation.x = 0.12;

      const core = new THREE.Mesh(
        new THREE.SphereGeometry(density === 'hero' ? 0.18 : 0.14, 20, 20),
        new THREE.MeshStandardMaterial({
          color: '#ffe2d2',
          emissive: '#ffa575',
          emissiveIntensity: density === 'hero' ? 1.05 : 0.7,
        })
      );

      const ambient = new THREE.AmbientLight('#d6bcfa', 0.65);
      const pointA = new THREE.PointLight('#c084fc', density === 'hero' ? 1.15 : 0.8, 20);
      pointA.position.set(2.8, 2.2, 3.4);
      const pointB = new THREE.PointLight('#f5d0fe', density === 'hero' ? 0.55 : 0.35, 16);
      pointB.position.set(-2.2, -1.2, 2.8);

      galaxyGroup.add(galaxyPoints, core);
      scene.add(galaxyGroup, ambient, pointA, pointB);

      const fieldGeometry = new THREE.BufferGeometry();
      const fieldCount = density === 'hero' ? 1200 : 320;
      const fieldPositions = new Float32Array(fieldCount * 3);

      for (let i = 0; i < fieldCount; i += 1) {
        const i3 = i * 3;
        const radius = 8 + Math.random() * 8;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        fieldPositions[i3] = radius * Math.sin(phi) * Math.cos(theta);
        fieldPositions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
        fieldPositions[i3 + 2] = radius * Math.cos(phi);
      }

      fieldGeometry.setAttribute('position', new THREE.BufferAttribute(fieldPositions, 3));
      const starField = new THREE.Points(
        fieldGeometry,
        new THREE.PointsMaterial({
          color: '#f5e9ff',
          size: density === 'hero' ? 0.02 : 0.015,
          transparent: true,
          opacity: density === 'hero' ? 0.45 : 0.35,
        })
      );
      scene.add(starField);

      let rafId = 0;
      const animate = () => {
        galaxyGroup.rotation.y += density === 'hero' ? 0.0015 : 0.0013;
        galaxyGroup.rotation.z += density === 'hero' ? 0.00035 : 0.00027;
        core.position.y = Math.sin(performance.now() * 0.0008) * 0.06;
        starField.rotation.y += density === 'hero' ? 0.00012 : 0.0001;

        if (hasRenderableSize()) {
          renderer.render(scene, camera);
        }
        rafId = requestAnimationFrame(animate);
      };

      animate();

      const onResize = () => {
        const w = mount.clientWidth;
        const h = mount.clientHeight;
        if (w <= 1 || h <= 1) {
          return;
        }
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
      };

      window.addEventListener('resize', onResize);

      return () => {
        window.removeEventListener('resize', onResize);
        cancelAnimationFrame(rafId);
        galaxyGeometry.dispose();
        galaxyMaterial.dispose();
        fieldGeometry.dispose();
        scene.clear();
        renderer.dispose();
        if (renderer.domElement.parentElement === mount) {
          mount.removeChild(renderer.domElement);
        }
      };
    };

    const initWebGPU = async (): Promise<Cleanup> => {
      const THREE_WEBGPU = await import('three/webgpu');
      const TSL = await import('three/tsl');

      let OrbitControlsCtor: any = null;
      if (density === 'hero') {
        const controlsModule = await import('three/addons/controls/OrbitControls.js');
        OrbitControlsCtor = controlsModule.OrbitControls;
      }

      const {
        color,
        cos,
        float,
        mix,
        range,
        sin,
        time,
        uniform,
        uv,
        vec3,
        vec4,
      } = TSL;

      const twoPi = float(Math.PI * 2);

      const { width, height } = getSafeSize();

      const camera = new THREE_WEBGPU.PerspectiveCamera(50, width / height, 0.1, 100);
      camera.position.set(
        density === 'hero' ? 4 : 3,
        density === 'hero' ? 2 : 1.55,
        density === 'hero' ? 5 : 4
      );

      const scene = new THREE_WEBGPU.Scene();

      const material = new THREE_WEBGPU.SpriteNodeMaterial({
        depthWrite: false,
        blending: THREE_WEBGPU.AdditiveBlending,
      });

      const size = uniform(density === 'hero' ? 0.08 : 0.06);
      material.scaleNode = range(0, 1).mul(size);

      const radiusRatio = range(0, 1);
      const radius = radiusRatio.pow(1.5).mul(density === 'hero' ? 5 : 4).toVar();

      const branches = 3;
      const branchAngle = range(0, branches).floor().mul(twoPi.div(branches));
      const angle = branchAngle.add(time.mul(radiusRatio.oneMinus()));

      const position = vec3(cos(angle), 0, sin(angle)).mul(radius);
      const randomOffset = range(vec3(-1), vec3(1)).pow3().mul(radiusRatio).add(0.2);

      material.positionNode = position.add(randomOffset);

      const colorInside = uniform(color('#ffa575'));
      const colorOutside = uniform(color('#311599'));
      const colorFinal = mix(colorInside, colorOutside, radiusRatio.oneMinus().pow(2).oneMinus());
      const alpha = float(density === 'hero' ? 0.11 : 0.1).div(uv().sub(0.5).length()).sub(0.2);
      material.colorNode = vec4(colorFinal, alpha);

      const mesh = new THREE_WEBGPU.InstancedMesh(
        new THREE_WEBGPU.PlaneGeometry(1, 1),
        material,
        density === 'hero' ? 20000 : 9000
      );
      mesh.rotation.x = 0.08;
      scene.add(mesh);

      const renderer = new THREE_WEBGPU.WebGPURenderer({ antialias: true, alpha: true });
      if (typeof (renderer as any).init === 'function') {
        await (renderer as any).init();
      }
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setSize(width, height);
      renderer.setClearColor(0x000000, 0);
      mount.appendChild(renderer.domElement);

      let controls: any = null;
      if (OrbitControlsCtor) {
        controls = new OrbitControlsCtor(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.enablePan = false;
        controls.minDistance = 0.1;
        controls.maxDistance = 50;
        controls.autoRotate = true;
        controls.autoRotateSpeed = 0.35;
      }

      const onResize = () => {
        const w = mount.clientWidth;
        const h = mount.clientHeight;
        if (w <= 1 || h <= 1) {
          return;
        }

        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
      };

      window.addEventListener('resize', onResize);

      let fallbackCleanup: Cleanup | null = null;
      let webgpuDisposed = false;

      const disposeWebGPU = () => {
        if (webgpuDisposed) {
          return;
        }

        webgpuDisposed = true;
        window.removeEventListener('resize', onResize);
        renderer.setAnimationLoop(null);
        controls?.dispose?.();
        scene.clear();
        renderer.dispose();
        if (renderer.domElement.parentElement === mount) {
          mount.removeChild(renderer.domElement);
        }
      };

      const animate = () => {
        try {
          if (!controls) {
            mesh.rotation.y += density === 'hero' ? 0.001 : 0.00125;
          } else {
            controls.update();
          }

          if (hasRenderableSize()) {
            renderer.render(scene, camera);
          }
        } catch (error) {
          console.warn('WebGPU render failed. Switching to WebGL fallback scene.', error);
          disposeWebGPU();
          fallbackCleanup = initWebGLFallback();
        }
      };

      renderer.setAnimationLoop(animate);

      return () => {
        disposeWebGPU();
        fallbackCleanup?.();
      };
    };

    const supportsWebGPU = density === 'hero' && typeof navigator !== 'undefined' && 'gpu' in navigator;

    let cleanupScene: Cleanup | null = null;
    let disposed = false;

    const setup = async () => {
      if (supportsWebGPU) {
        try {
          cleanupScene = await initWebGPU();
          if (disposed) {
            cleanupScene();
          }
          return;
        } catch (error) {
          console.warn('Falling back to WebGL galaxy scene.', error);
        }
      }

      cleanupScene = initWebGLFallback();
      if (disposed) {
        cleanupScene();
      }
    };

    void setup();

    return () => {
      disposed = true;
      cleanupScene?.();
    };
  }, [density]);

  return <div ref={mountRef} className={className || 'h-[360px] w-full md:h-[460px]'} />;
};
