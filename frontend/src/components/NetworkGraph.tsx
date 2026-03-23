'use client';

type Device = { id: string; ip: string; status: string };

type NetworkGraphProps = { devices: Device[] };

export function NetworkGraph({ devices }: NetworkGraphProps) {
  const n = devices.length;
  const r = 120;
  const cx = 180;
  const cy = 120;

  const nodes = devices.map((d, i) => {
    const angle = (2 * Math.PI * i) / Math.max(n, 1);
    return {
      ...d,
      x: cx + r * Math.cos(angle),
      y: cy + r * Math.sin(angle),
    };
  });

  return (
    <div className="h-64 relative bg-dark-900/50 rounded overflow-hidden">
      <svg viewBox="0 0 360 240" className="w-full h-full">
        {nodes.map((a, i) =>
          nodes.map((b, j) =>
            i < j ? (
              <line
                key={`${i}-${j}`}
                x1={a.x}
                y1={a.y}
                x2={b.x}
                y2={b.y}
                stroke="#30363d"
                strokeWidth={1}
              />
            ) : null
          )
        )}
        {nodes.map((d) => (
          <g key={d.id}>
            <circle
              cx={d.x}
              cy={d.y}
              r={12}
              fill={d.status === 'online' ? '#14b8a6' : '#64748b'}
              stroke="#0d9488"
              strokeWidth={2}
            />
            <text
              x={d.x}
              y={d.y + 24}
              textAnchor="middle"
              fill="#8b949e"
              fontSize={10}
              fontFamily="monospace"
            >
              {d.ip}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
