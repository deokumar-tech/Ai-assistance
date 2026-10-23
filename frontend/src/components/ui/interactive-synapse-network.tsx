import { useEffect, useRef, type ReactNode } from "react";

export interface InteractiveSynapseNetworkProps {
  children?: ReactNode;
  nodeColor?: string;
  pulseColor?: string;
  nodeCount?: number;
  connectionRadius?: number;
  trailOpacity?: number;
  ariaLabel?: string;
  className?: string;
}

interface SynapseNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  connections: SynapseNode[];
  pulses: Array<{ end: SynapseNode; progress: number }>;
  activation: number;
}

export default function InteractiveSynapseNetwork({
  children,
  nodeColor = "rgba(0,220,255,0.8)",
  pulseColor = "rgba(255,255,255,1)",
  nodeCount = 50,
  connectionRadius = 200,
  trailOpacity = 0.2,
  ariaLabel = "Interactive synapse network",
  className = "",
}: InteractiveSynapseNetworkProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: -9999, y: -9999 });

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);
    const nodes: SynapseNode[] = Array.from({ length: nodeCount }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      radius: Math.random() * 2 + 2,
      connections: [],
      pulses: [],
      activation: 0,
    }));

    nodes.forEach((node) => {
      nodes.forEach((other) => {
        if (node !== other && Math.hypot(node.x - other.x, node.y - other.y) < connectionRadius) {
          node.connections.push(other);
        }
      });
    });

    const onMouseMove = (event: MouseEvent) => {
      mouseRef.current = { x: event.clientX, y: event.clientY };
    };
    const onMouseLeave = () => {
      mouseRef.current = { x: -9999, y: -9999 };
    };
    const onResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseleave", onMouseLeave);
    window.addEventListener("resize", onResize);

    let frameId = 0;
    const animate = () => {
      context.fillStyle = `rgba(0,15,25,${trailOpacity})`;
      context.fillRect(0, 0, width, height);

      nodes.forEach((node) => {
        node.connections.forEach((other) => {
          const alpha = Math.max(0.05, node.activation, other.activation) * 0.2;
          context.beginPath();
          context.moveTo(node.x, node.y);
          context.lineTo(other.x, other.y);
          context.strokeStyle = `rgba(0,220,255,${alpha})`;
          context.stroke();
        });
      });

      nodes.forEach((node) => {
        node.x += node.vx;
        node.y += node.vy;
        if (node.x < 0 || node.x > width) node.vx *= -1;
        if (node.y < 0 || node.y > height) node.vy *= -1;

        const distance = Math.hypot(node.x - mouseRef.current.x, node.y - mouseRef.current.y);
        const target = Math.max(0, 1 - distance / (connectionRadius * 0.8));
        node.activation += (target - node.activation) * 0.1;

        if (node.activation > 0.5 && node.connections.length && Math.random() > 0.98) {
          const end = node.connections[Math.floor(Math.random() * node.connections.length)];
          if (end) node.pulses.push({ end, progress: 0 });
        }

        node.pulses = node.pulses.filter((pulse) => pulse.progress < 1);
        node.pulses.forEach((pulse) => {
          pulse.progress += 0.03;
          const x = node.x + (pulse.end.x - node.x) * pulse.progress;
          const y = node.y + (pulse.end.y - node.y) * pulse.progress;
          context.beginPath();
          context.arc(x, y, 3, 0, Math.PI * 2);
          context.fillStyle = pulseColor;
          context.fill();
        });

        context.beginPath();
        context.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        context.globalAlpha = Math.max(0.2, node.activation);
        context.fillStyle = nodeColor;
        context.fill();
        context.globalAlpha = 1;
      });

      frameId = requestAnimationFrame(animate);
    };

    animate();
    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseleave", onMouseLeave);
      window.removeEventListener("resize", onResize);
    };
  }, [connectionRadius, nodeColor, nodeCount, pulseColor, trailOpacity]);

  return (
    <div
      role="region"
      className={`relative h-screen w-screen overflow-hidden bg-[hsl(var(--network-bg))] ${className}`}
      aria-label={ariaLabel}
    >
      <canvas ref={canvasRef} aria-hidden="true" className="absolute inset-0 block h-full w-full" />
      <div className="relative z-10 h-full w-full">{children}</div>
    </div>
  );
}
