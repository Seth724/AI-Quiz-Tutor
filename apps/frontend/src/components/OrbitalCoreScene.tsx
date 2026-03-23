'use client';

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface OrbitalCoreSceneProps {
  className?: string;
  density?: 'ambient' | 'feature';
}

export const OrbitalCoreScene = ({ className, density = 'ambient' }: OrbitalCoreSceneProps) => {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) {
      return;
    }

    const hasRenderableSize = () => mount.clientWidth > 1 && mount.clientHeight > 1;
    if (!hasRenderableSize()) {
      return;
    }

    const width = mount.clientWidth;
    const height = mount.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100);
    camera.position.set(0, 0.18, density === 'ambient' ? 5.6 : 4.6);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.setClearColor(0x000000, 0);
    mount.appendChild(renderer.domElement);

    const modelGroup = new THREE.Group();
    scene.add(modelGroup);

    const ambientLight = new THREE.AmbientLight('#c4b5fd', 0.92);
    const keyLight = new THREE.PointLight('#a855f7', density === 'ambient' ? 1.2 : 1.45, 18);
    keyLight.position.set(2.8, 2.1, 3.2);
    const rimLight = new THREE.PointLight('#f5d0fe', density === 'ambient' ? 0.58 : 0.76, 14);
    rimLight.position.set(-2.4, -1.4, 2.8);
    scene.add(ambientLight, keyLight, rimLight);

    const coreGeometry = new THREE.IcosahedronGeometry(density === 'ambient' ? 1.02 : 1.18, 5);
    const coreMaterial = new THREE.MeshPhysicalMaterial({
      color: '#dec7ff',
      emissive: '#7c3aed',
      emissiveIntensity: density === 'ambient' ? 0.84 : 1.05,
      roughness: 0.24,
      metalness: 0.08,
      transmission: 0.25,
      thickness: 0.8,
      transparent: true,
      opacity: density === 'ambient' ? 0.86 : 0.92,
      clearcoat: 1,
      clearcoatRoughness: 0.12,
    });
    const coreMesh = new THREE.Mesh(coreGeometry, coreMaterial);
    modelGroup.add(coreMesh);

    const shellGeometry = new THREE.SphereGeometry(density === 'ambient' ? 1.6 : 1.75, 40, 40);
    const shellMaterial = new THREE.MeshBasicMaterial({
      color: '#a855f7',
      transparent: true,
      opacity: density === 'ambient' ? 0.08 : 0.11,
      blending: THREE.AdditiveBlending,
    });
    const shellMesh = new THREE.Mesh(shellGeometry, shellMaterial);
    modelGroup.add(shellMesh);

    const haloCount = density === 'ambient' ? 1800 : 2600;
    const haloPositions = new Float32Array(haloCount * 3);
    const haloColors = new Float32Array(haloCount * 3);
    const haloInside = new THREE.Color('#fbcfe8');
    const haloOutside = new THREE.Color('#4c1d95');

    for (let i = 0; i < haloCount; i += 1) {
      const i3 = i * 3;
      const radius = 1.65 + Math.random() * 2.4;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      const x = Math.cos(theta) * Math.sin(phi) * radius * 1.32;
      const y = Math.cos(phi) * radius * 0.82;
      const z = Math.sin(theta) * Math.sin(phi) * radius;

      haloPositions[i3] = x;
      haloPositions[i3 + 1] = y;
      haloPositions[i3 + 2] = z;

      const mixed = haloInside.clone();
      mixed.lerp(haloOutside, Math.min(radius / 4.2, 1));
      haloColors[i3] = mixed.r;
      haloColors[i3 + 1] = mixed.g;
      haloColors[i3 + 2] = mixed.b;
    }

    const haloGeometry = new THREE.BufferGeometry();
    haloGeometry.setAttribute('position', new THREE.BufferAttribute(haloPositions, 3));
    haloGeometry.setAttribute('color', new THREE.BufferAttribute(haloColors, 3));

    const haloMaterial = new THREE.PointsMaterial({
      size: density === 'ambient' ? 0.022 : 0.028,
      sizeAttenuation: true,
      depthWrite: false,
      transparent: true,
      opacity: density === 'ambient' ? 0.58 : 0.72,
      blending: THREE.AdditiveBlending,
      vertexColors: true,
    });

    const haloPoints = new THREE.Points(haloGeometry, haloMaterial);
    modelGroup.add(haloPoints);

    const orbitGroup = new THREE.Group();
    modelGroup.add(orbitGroup);

    const satelliteGeometry = new THREE.SphereGeometry(0.07, 14, 14);
    const satelliteMaterialA = new THREE.MeshStandardMaterial({
      color: '#f5d0fe',
      emissive: '#d946ef',
      emissiveIntensity: 1.1,
      roughness: 0.3,
      metalness: 0.1,
    });
    const satelliteMaterialB = new THREE.MeshStandardMaterial({
      color: '#c4b5fd',
      emissive: '#8b5cf6',
      emissiveIntensity: 0.9,
      roughness: 0.33,
      metalness: 0.14,
    });

    const satelliteA = new THREE.Mesh(satelliteGeometry, satelliteMaterialA);
    const satelliteB = new THREE.Mesh(satelliteGeometry, satelliteMaterialB);
    orbitGroup.add(satelliteA, satelliteB);

    let rafId = 0;

    const animate = () => {
      const t = performance.now() * 0.001;

      modelGroup.rotation.y += density === 'ambient' ? 0.0034 : 0.0042;
      modelGroup.rotation.x = Math.sin(t * 0.42) * 0.1;

      coreMesh.rotation.x += 0.0013;
      coreMesh.rotation.y += 0.0027;
      const corePulse = 1 + Math.sin(t * 1.7) * 0.03;
      coreMesh.scale.setScalar(corePulse);

      const shellPulse = 1 + Math.sin(t * 1.25 + 1.1) * 0.06;
      shellMesh.scale.setScalar(shellPulse);

      satelliteA.position.set(Math.cos(t * 1.35) * 2.18, Math.sin(t * 1.8) * 0.42, Math.sin(t * 1.35) * 1.32);
      satelliteB.position.set(Math.cos(t * 0.92 + 1.2) * -1.88, Math.sin(t * 1.24 + 0.6) * 0.36, Math.sin(t * 0.92 + 1.2) * 1.06);

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

      coreGeometry.dispose();
      coreMaterial.dispose();
      shellGeometry.dispose();
      shellMaterial.dispose();
      haloGeometry.dispose();
      haloMaterial.dispose();
      satelliteGeometry.dispose();
      satelliteMaterialA.dispose();
      satelliteMaterialB.dispose();

      scene.clear();
      renderer.dispose();

      if (renderer.domElement.parentElement === mount) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, [density]);

  return <div ref={mountRef} className={className || 'h-[340px] w-full md:h-[420px]'} />;
};
