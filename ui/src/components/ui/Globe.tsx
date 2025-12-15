'use client';

import createGlobe from 'cobe';
import { useEffect, useRef } from 'react';
import { useSpring } from 'react-spring';

interface GlobeProps {
    selectedCountry?: string;
    onSelectCountry?: (country: string) => void;
    availableCountries?: string[];
}

export function Globe({ selectedCountry = 'all', onSelectCountry, availableCountries }: GlobeProps) {
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

    const allLocations = [
        // North America
        { name: 'US', location: [37.0902, -95.7129], size: 0.1 },
        { name: 'CA', location: [56.1304, -106.3468], size: 0.08 },
        { name: 'MX', location: [23.6345, -102.5528], size: 0.07 },
        
        // South America
        { name: 'BR', location: [-14.2350, -51.9253], size: 0.08 },
        { name: 'AR', location: [-38.4161, -63.6167], size: 0.06 },
        { name: 'CL', location: [-35.6751, -71.5430], size: 0.05 },
        
        // Europe
        { name: 'UK', location: [55.3781, -3.4360], size: 0.06 },
        { name: 'DE', location: [51.1657, 10.4515], size: 0.06 },
        { name: 'FR', location: [46.2276, 2.2137], size: 0.06 },
        { name: 'ES', location: [40.4637, -3.7492], size: 0.06 },
        { name: 'IT', location: [41.8719, 12.5674], size: 0.06 },
        { name: 'NL', location: [52.1326, 5.2913], size: 0.04 },
        { name: 'SE', location: [60.1282, 18.6435], size: 0.05 },
        { name: 'PL', location: [51.9194, 19.1451], size: 0.05 },
        { name: 'CH', location: [46.8182, 8.2275], size: 0.04 },
        
        // Asia
        { name: 'IN', location: [20.5937, 78.9629], size: 0.1 },
        { name: 'CN', location: [35.8617, 104.1954], size: 0.1 },
        { name: 'JP', location: [36.2048, 138.2529], size: 0.07 },
        { name: 'KR', location: [35.9078, 127.7669], size: 0.05 },
        { name: 'SG', location: [1.3521, 103.8198], size: 0.04 },
        { name: 'TH', location: [15.8700, 100.9925], size: 0.05 },
        { name: 'ID', location: [-0.7893, 113.9213], size: 0.07 },
        { name: 'PH', location: [12.8797, 121.7740], size: 0.05 },
        { name: 'VN', location: [14.0583, 108.2772], size: 0.05 },
        { name: 'MY', location: [4.2105, 101.9758], size: 0.05 },
        { name: 'AE', location: [23.4241, 53.8478], size: 0.04 },
        { name: 'IL', location: [31.0461, 34.8516], size: 0.04 },
        
        // Oceania
        { name: 'AU', location: [-25.2744, 133.7751], size: 0.08 },
        { name: 'NZ', location: [-40.9006, 174.8860], size: 0.05 },
        
        // Africa
        { name: 'ZA', location: [-30.5595, 22.9375], size: 0.06 },
        { name: 'NG', location: [9.0820, 8.6753], size: 0.06 },
        { name: 'EG', location: [26.8206, 30.8025], size: 0.05 },
        { name: 'KE', location: [-0.0236, 37.9062], size: 0.04 },
    ];

    const locations = availableCountries
        ? allLocations.filter(loc => availableCountries.includes(loc.name))
        : allLocations;

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
    }, [locations]);

    const handleCountryClick = (country: string) => {
        if (onSelectCountry) {
            if (selectedCountry === country) {
                onSelectCountry('all');
            } else {
                onSelectCountry(country);
            }
        }
    };

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

            {onSelectCountry && locations.length > 0 && (
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
                            onClick={() => handleCountryClick(loc.name)}
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
