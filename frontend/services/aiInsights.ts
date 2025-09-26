import axios from 'axios';

export interface PropertyInsights {
  neighborhood: string;
  commute: string;
  lifestyle: string;
  schools: string;
}

export interface PropertyInsightRequest {
  city: string;
  state: string;
  price?: number;
  bedrooms?: number;
  bathrooms?: number;
  square_feet?: number;
  property_type?: string;
  search_type?: string;
}

class AIInsightsService {
  private baseURL = 'http://127.0.0.1:8000/api/v1';

  async generatePropertyInsights(property: PropertyInsightRequest): Promise<PropertyInsights> {
    try {
      const response = await axios.post(`${this.baseURL}/property-insights`, property);
      return response.data;
    } catch (error) {
      console.error('Error generating AI insights:', error);

      // Return fallback insights if API fails
      return this.generateFallbackInsights(property);
    }
  }

  private generateFallbackInsights(property: PropertyInsightRequest): PropertyInsights {
    const city = property.city || 'Unknown';
    const isUrban = ['downtown', 'city', 'metro'].some(term =>
      city.toLowerCase().includes(term)
    );

    return {
      neighborhood: `${isUrban ? 'Urban' : 'Suburban'} area in ${city}`,
      commute: `Typical ${isUrban ? 'urban' : 'suburban'} commute patterns`,
      lifestyle: `Standard ${isUrban ? 'city' : 'suburban'} amenities nearby`,
      schools: `Research local school districts in ${city}`
    };
  }

  // Cache for insights to avoid repeated API calls for same property
  private insightsCache = new Map<string, PropertyInsights>();

  async getCachedInsights(property: PropertyInsightRequest): Promise<PropertyInsights> {
    const cacheKey = `${property.city}-${property.state}-${property.bedrooms || 'any'}-${property.search_type || 'rent'}`;

    if (this.insightsCache.has(cacheKey)) {
      return this.insightsCache.get(cacheKey)!;
    }

    const insights = await this.generatePropertyInsights(property);
    this.insightsCache.set(cacheKey, insights);

    return insights;
  }
}

export const aiInsightsService = new AIInsightsService();