import { useEffect, useState } from 'react';
import { calculateStars } from 'astronomy-engine';
import { LocationObject } from 'expo-location';

interface StarData {
    id: string;
    name: string;
    x: number;
    y: number;
    z: number;
    magnitude: number;
    color: string;
    size: number;
}

interface Constellation {
    name: string;
    stars: Array<{
        from: [number, number, number];
        to: [number, number, number];
    }>;
    labelPosition: [number, number, number];
}

export function useStars(location: LocationObject | null, date: Date) {
    const [stars, setStars] = useState<StarData[]>([]);
    const [constellations, setConstellations] = useState<Constellation[]>([]);

    useEffect(() => {
        if (!location) return;

        // Calculate visible stars
        const visibleStars = calculateStars(
            date,
            location.coords.latitude,
            location.coords.longitude
        );

        const starData: StarData[] = visibleStars.map(star => ({
            id: `star-${star.id}`,
            name: star.name,
            x: star.x * 100,
            y: star.y * 100,
            z: star.z * 100,
            magnitude: star.magnitude,
            color: getStarColor(star.temperature),
            size: getStarSize(star.magnitude),
        }));

        setStars(starData);

        // Generate constellations
        const constellationsData: Constellation[] = [
            {
                name: 'Ursa Major',
                stars: [
                    { from: [10, 20, 30], to: [15, 25, 35] },
                    // More constellation lines...
                ],
                labelPosition: [12, 22, 32]
            },
            // More constellations...
        ];
        setConstellations(constellationsData);
    }, [location, date]);

    return { stars, constellations };
}

function getStarColor(temperature: number): string {
    if (temperature > 10000) return '#9bb0ff'; // Blue
    if (temperature > 7500) return '#aabfff'; // Blue-white
    if (temperature > 6000) return '#cad7ff'; // White
    if (temperature > 5000) return '#f8f7ff'; // Yellow-white
    if (temperature > 3500) return '#ffd3a0'; // Yellow
    if (temperature > 2000) return '#ffb36b'; // Orange
    return '#ff8b60'; // Red
}

function getStarSize(magnitude: number): number {
    return Math.max(0.1, 1 - magnitude / 10);
}