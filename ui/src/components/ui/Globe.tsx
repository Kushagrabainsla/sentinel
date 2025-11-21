'use client';

import createGlobe from 'cobe';
import { useEffect, useRef } from 'react';
import { useSpring } from 'react-spring';

interface GlobeProps {
    selectedCountry?: string;
    onSelectCountry?: (country: string) => void;
}

export function Globe({ selectedCountry = 'all', onSelectCountry }: GlobeProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const pointerInteracting = useRef<number | null>(null);
    const pointerInteractionMovement = useRef(0);
    const [{ r }, api] = useSpring(() => ({
        r: 0,
        config: {
            mass: 1,
            tension: 280,
            friction: 40,
            precision: 0.001,
        },
    }));

    const locations = [
        { name: 'US', location: [40, -100], size: 0.1 },
        { name: 'UK', location: [51.5, -0.1], size: 0.05 },
        { name: 'CA', location: [60, -100], size: 0.1 },
        { name: 'DE', location: [51, 10], size: 0.05 },
        { name: 'FR', location: [46, 2], size: 0.05 },
        { name: 'AU', location: [-25, 133], size: 0.1 },
        { name: 'IN', location: [20, 77], size: 0.1 },
    ];

    useEffect(() => {
        let phi = 0;
        let width = 0;
        const onResize = () => canvasRef.current && (width = canvasRef.current.offsetWidth);
        window.addEventListener('resize', onResize);
        onResize();
        const globe = createGlobe(canvasRef.current!, {
            devicePixelRatio: 2,
            width: width * 2,
            height: width * 2,
            phi: 0,
            theta: 0.3,
            dark: 1,
            diffuse: 1.2,
            mapSamples: 16000,
            mapBrightness: 6,
            baseColor: [0.3, 0.3, 0.3],
            markerColor: [0.1, 0.8, 1],
            glowColor: [1, 1, 1],
            markers: locations.map((loc) => ({ location: loc.location as [number, number], size: loc.size })),
            onRender: (state) => {
                // Called on every animation frame.
                // `state` will be an empty object, return updated params.
                state.phi = phi + r.get();
                phi += 0.003;
                state.width = width * 2;
                state.height = width * 2;
            },
        });
        setTimeout(() => (canvasRef.current!.style.opacity = '1'));
        return () => {
            globe.destroy();
            window.removeEventListener('resize', onResize);
        };
    }, []);

    return (
        <div className="relative w-full max-w-[400px] mx-auto aspect-square">
            <canvas
                ref={canvasRef}
                style={{ width: '100%', height: '100%', contain: 'layout paint size', opacity: 0, transition: 'opacity 1s ease' }}
                onPointerDown={(e) => {
                    pointerInteracting.current = e.clientX - pointerInteractionMovement.current;
                    canvasRef.current!.style.cursor = 'grabbing';
                }}
                onPointerUp={() => {
                    pointerInteracting.current = null;
                    canvasRef.current!.style.cursor = 'grab';
                }}
                onPointerOut={() => {
                    pointerInteracting.current = null;
                    canvasRef.current!.style.cursor = 'grab';
                }}
                onMouseMove={(e) => {
                    if (pointerInteracting.current !== null) {
                        const delta = e.clientX - pointerInteracting.current;
                        pointerInteractionMovement.current = delta;
                        api.start({
                            r: delta / 200,
                        });
                    }
                }}
                onTouchMove={(e) => {
                    if (pointerInteracting.current !== null && e.touches[0]) {
                        const delta = e.touches[0].clientX - pointerInteracting.current;
                        pointerInteractionMovement.current = delta;
                        api.start({
                            r: delta / 100,
                        });
                    }
                }}
            />

            {/* Overlay Controls for Country Selection */}
            {onSelectCountry && (
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex flex-wrap justify-center gap-2 w-full px-4">
                    <button
                        onClick={() => onSelectCountry('all')}
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${selectedCountry === 'all'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-background/80 backdrop-blur-sm border border-border hover:bg-accent'
                            }`}
                    >
                        All
                    </button>
                    {locations.map((loc) => (
                        <button
                            key={loc.name}
                            onClick={() => onSelectCountry(loc.name)}
                            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${selectedCountry === loc.name
                                ? 'bg-primary text-primary-foreground'
                                : 'bg-background/80 backdrop-blur-sm border border-border hover:bg-accent'
                                }`}
                        >
                            {loc.name}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
