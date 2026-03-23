'use client';

import { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  size: number;
  alpha: number;
  decay: number;
  offsetX: number;
  offsetY: number;
}

export default function CursorTrail() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const animationRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const createParticle = (x: number, y: number) => {
      const count = Math.floor(Math.random() * 3) + 1;
      for (let i = 0; i < count; i++) {
        particlesRef.current.push({
          x,
          y,
          size: Math.random() * 2 + 0.5,
          alpha: Math.random() * 0.5 + 0.5,
          decay: Math.random() * 0.02 + 0.015,
          offsetX: (Math.random() - 0.5) * 20,
          offsetY: (Math.random() - 0.5) * 20,
        });
      }
    };

    const handleMouseMove = (e: MouseEvent) => {
      createParticle(e.clientX, e.clientY);
    };

    window.addEventListener('mousemove', handleMouseMove);

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particlesRef.current = particlesRef.current.filter((particle) => {
        particle.alpha -= particle.decay;
        if (particle.alpha <= 0) return false;

        ctx.save();
        ctx.globalAlpha = particle.alpha;
        ctx.fillStyle = '#ffffff';
        ctx.shadowBlur = particle.size * 2;
        ctx.shadowColor = '#a78bfa';

        const drawX = particle.x + particle.offsetX * (1 - particle.alpha);
        const drawY = particle.y + particle.offsetY * (1 - particle.alpha);

        ctx.beginPath();
        const spikes = 4;
        const outerRadius = particle.size;
        const innerRadius = particle.size * 0.4;

        for (let i = 0; i < spikes * 2; i++) {
          const radius = i % 2 === 0 ? outerRadius : innerRadius;
          const angle = (i * Math.PI) / spikes - Math.PI / 2;
          const x = drawX + Math.cos(angle) * radius;
          const y = drawY + Math.sin(angle) * radius;

          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }

        ctx.closePath();
        ctx.fill();
        ctx.restore();

        return true;
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animationRef.current);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none fixed inset-0 z-[90] hidden lg:block"
      style={{ mixBlendMode: 'screen' }}
    />
  );
}
