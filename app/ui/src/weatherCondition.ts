export type WeatherCondition = 'clear' | 'mainly-clear' | 'partly-cloudy' | 'overcast' | 'fog'
 | 'drizzle' | 'freezing-drizzle' | 'rain' | 'freezing-rain' | 'snow' | 'rain-showers'
 | 'snow-showers' | 'thunder' | 'thunder-hail' | 'missing' | 'unknown';

// Provider WMO interpretation: https://open-meteo.com/en/docs#weather_variable_documentation
const conditions: Readonly<Record<number, WeatherCondition>> = {
 0:'clear', 1:'mainly-clear', 2:'partly-cloudy', 3:'overcast', 45:'fog', 48:'fog',
 51:'drizzle', 53:'drizzle', 55:'drizzle', 56:'freezing-drizzle', 57:'freezing-drizzle',
 61:'rain', 63:'rain', 65:'rain', 66:'freezing-rain', 67:'freezing-rain',
 71:'snow', 73:'snow', 75:'snow', 77:'snow', 80:'rain-showers', 81:'rain-showers', 82:'rain-showers',
 85:'snow-showers', 86:'snow-showers', 95:'thunder', 97:'thunder', 96:'thunder-hail', 99:'thunder-hail',
};

export function weatherCondition(code: unknown): WeatherCondition {
 if(code === null || code === undefined) return 'missing';
 if(typeof code !== 'number' || !Number.isInteger(code)) return 'unknown';
 return conditions[code] ?? 'unknown';
}

export function weatherIsNight(isDay?: boolean | number | null): boolean {
 return isDay === false || isDay === 0;
}
