import React, { useState, useEffect } from 'react';
import { aiInsightsService, PropertyInsights } from '@/services/aiInsights';

interface Listing {
  id: number;
  title: string;
  price: number;
  price_range?: string;
  bedrooms: number;
  bathrooms: number;
  square_feet: number;
  city: string;
  state: string;
  address?: string;        // ✅ ADD THIS
  full_address?: string; 
  url?: string;
  description?: string;
  photo_url?: string;
  photos?: string[];
}

interface PropertyCardProps {
  listing: Listing;
  searchType: string;
  formatPrice: (price: number) => string;
}

const PropertyCard: React.FC<PropertyCardProps> = ({ listing, searchType, formatPrice }) => {
  // Default placeholder image for properties without photos
  const defaultPlaceholder = 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400&h=300&fit=crop&auto=format&q=80';

  const [isSaved, setIsSaved] = useState(false);
  const [insights, setInsights] = useState<PropertyInsights | null>(null);
  const [loadingInsights, setLoadingInsights] = useState(true);

  // Check if property is already saved on mount
  useEffect(() => {
    const savedProperties = JSON.parse(localStorage.getItem('savedProperties') || '[]');
    setIsSaved(savedProperties.some((saved: Listing) => saved.id === listing.id));
  }, [listing.id]);

  // Generate AI insights for the property
  useEffect(() => {
    const generateInsights = async () => {
      if (!listing.city || !listing.state) {
        setLoadingInsights(false);
        return;
      }

      try {
        const propertyData = {
          city: listing.city,
          state: listing.state,
          address: listing.address || listing.full_address || undefined,
          price: listing.price || undefined,
          bedrooms: listing.bedrooms || undefined,
          bathrooms: listing.bathrooms || undefined,
          square_feet: listing.square_feet || undefined,
          property_type: 'property',
          search_type: searchType
        };

        const aiInsights = await aiInsightsService.getCachedInsights(propertyData);
        setInsights(aiInsights);
      } catch (error) {
        console.error('Failed to generate insights:', error);
      } finally {
        setLoadingInsights(false);
      }
    };

    generateInsights();
  }, [listing, searchType]);

  const toggleSaved = () => {
    const savedProperties = JSON.parse(localStorage.getItem('savedProperties') || '[]');

    if (isSaved) {
      // Remove from saved
      const updatedSaved = savedProperties.filter((saved: Listing) => saved.id !== listing.id);
      localStorage.setItem('savedProperties', JSON.stringify(updatedSaved));
      setIsSaved(false);
    } else {
      // Add to saved
      const updatedSaved = [...savedProperties, listing];
      localStorage.setItem('savedProperties', JSON.stringify(updatedSaved));
      setIsSaved(true);
    }
  };


  return (
    <div className="group relative bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2 overflow-hidden border border-gray-100">
      {/* Property Image */}
      <div className="relative h-52 overflow-hidden group-hover:h-56 transition-all duration-500">
        <img
          src={listing.photo_url || defaultPlaceholder}
          alt={listing.title}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
          onError={(e) => {
            // If the main image fails, try the placeholder
            const target = e.target as HTMLImageElement;
            if (target.src !== defaultPlaceholder) {
              target.src = defaultPlaceholder;
            }
          }}
        />

        {/* Dark overlay for better text readability */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent"></div>

        {/* Save Button */}
        <button
          onClick={(e) => {
            e.preventDefault();
            toggleSaved();
          }}
          className={`absolute top-4 left-4 z-10 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-200 ${
            isSaved
              ? 'bg-red-500 hover:bg-red-600 text-white'
              : 'bg-white/90 hover:bg-white text-gray-700 hover:text-red-500'
          } shadow-lg backdrop-blur-sm`}
          title={isSaved ? 'Remove from saved' : 'Save property'}
        >
          <svg
            className="w-5 h-5"
            fill={isSaved ? 'currentColor' : 'none'}
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
            />
          </svg>
        </button>

        {/* Price Badge */}
        <div className="absolute top-4 right-4 z-10">
          <div className="bg-white/95 backdrop-blur-sm rounded-xl px-3 py-2 shadow-lg border border-white/20">
            <span className="text-lg font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              {listing.price_range
                ? listing.price_range
                : listing.price && listing.price > 0
                ? `${formatPrice(listing.price)}${searchType === 'rent' ? '/mo' : ''}`
                : "Contact"
              }
            </span>
          </div>
        </div>

        {/* Photo indicator */}
        {listing.photos && listing.photos.length > 1 && (
          <div className="absolute bottom-4 left-4 z-10">
            <div className="bg-black/50 backdrop-blur-sm rounded-lg px-2 py-1">
              <span className="text-white text-xs font-medium flex items-center">
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                </svg>
                {listing.photos.length}
              </span>
            </div>
          </div>
        )}

        {/* Visual indicator for placeholder vs real photo */}
        {!listing.photo_url && (
          <div className="absolute bottom-4 right-4 z-10">
            <div className="bg-black/30 backdrop-blur-sm rounded-lg px-2 py-1">
              <span className="text-white text-xs font-medium opacity-75">No Photo</span>
            </div>
          </div>
        )}
      </div>

      {/* Card Content */}
      <div className="p-6 space-y-4">
        {/* Title and Location */}
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-gray-900 line-clamp-2 group-hover:text-purple-600 transition-colors duration-200">
            {listing.title}
          </h3>
          <div className="flex items-center text-gray-600">
            <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span className="text-sm font-medium">{listing.city}, {listing.state}</span>
          </div>
        </div>

        {/* Property Details */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Bedrooms */}
            <div className="flex items-center text-gray-600">
              <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mr-2">
                <svg className="w-4 h-4 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3zM3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zM9.3 16.573A9.026 9.026 0 007 14.935v-3.957l1.818.78a3 3 0 002.364 0l5.508-2.361a11.026 11.026 0 01.25 3.762 1 1 0 01-.89.89 8.968 8.968 0 00-5.35 2.524 1 1 0 01-1.4 0zM6 18a1 1 0 001-1v-2.065a8.935 8.935 0 00-2-.712V17a1 1 0 001 1z"/>
                </svg>
              </div>
              <span className="text-sm font-medium">{listing.bedrooms} bed</span>
            </div>

            {/* Bathrooms */}
            <div className="flex items-center text-gray-600">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-2">
                <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M10 3v4h4V3z" />
                </svg>
              </div>
              <span className="text-sm font-medium">{listing.bathrooms} bath</span>
            </div>
          </div>

          {/* Square Footage */}
          {listing.square_feet && (
            <div className="flex items-center text-gray-600">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-2">
                <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
              </div>
              <span className="text-sm font-medium">{listing.square_feet.toLocaleString()} sq ft</span>
            </div>
          )}
        </div>

        {/* Description */}
        {listing.description && (
          <p className="text-gray-600 text-sm line-clamp-3 leading-relaxed">
            {listing.description}
          </p>
        )}

        {/* AI Insights Section - Enhanced with Real Data */}
        <div className="pt-4 border-t border-gray-100">
          <div className="mb-3">
            <h4 className="text-sm font-semibold text-gray-800 flex items-center">
              <div className="w-5 h-5 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center mr-2">
                <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                AI Insights
              </span>
              <span className="ml-2 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">
                Real Data
              </span>
            </h4>
          </div>

          {loadingInsights ? (
            <div className="space-y-2.5">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex items-center space-x-3 p-2 bg-gray-50 rounded-lg">
                  <div className="w-5 h-5 bg-gray-200 rounded-full animate-pulse"></div>
                  <div className="h-3 bg-gray-200 rounded animate-pulse flex-1"></div>
                </div>
              ))}
            </div>
          ) : insights ? (
            <div className="space-y-2.5">
              <div className="flex items-start space-x-3 p-2 bg-purple-50/50 rounded-lg border border-purple-100/50 hover:bg-purple-50 transition-colors duration-200">
                <span className="text-base mt-0.5">🏡</span>
                <div className="flex-1">
                  <p className="text-xs font-medium text-gray-800 leading-relaxed">{insights.neighborhood}</p>
                  <span className="text-xs text-purple-600 font-medium">Neighborhood</span>
                </div>
              </div>
              <div className="flex items-start space-x-3 p-2 bg-blue-50/50 rounded-lg border border-blue-100/50 hover:bg-blue-50 transition-colors duration-200">
                <span className="text-base mt-0.5">🚗</span>
                <div className="flex-1">
                  <p className="text-xs font-medium text-gray-800 leading-relaxed">{insights.commute}</p>
                  <span className="text-xs text-blue-600 font-medium">
                    {insights.commute.includes('Downtown') ? 'Commute to Downtown' : 'Commute'}
                  </span>
                </div>
              </div>
              <div className="flex items-start space-x-3 p-2 bg-green-50/50 rounded-lg border border-green-100/50 hover:bg-green-50 transition-colors duration-200">
                <span className="text-base mt-0.5">🛒</span>
                <div className="flex-1">
                  <p className="text-xs font-medium text-gray-800 leading-relaxed">{insights.lifestyle}</p>
                  <span className="text-xs text-green-600 font-medium">Lifestyle</span>
                </div>
              </div>
              <div className="flex items-start space-x-3 p-2 bg-orange-50/50 rounded-lg border border-orange-100/50 hover:bg-orange-50 transition-colors duration-200">
                <span className="text-base mt-0.5">🎓</span>
                <div className="flex-1">
                  <p className="text-xs font-medium text-gray-800 leading-relaxed">{insights.schools}</p>
                  <span className="text-xs text-orange-600 font-medium">Schools</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-gray-500 italic p-3 bg-gray-50 rounded-lg text-center">
              <svg className="w-4 h-4 mx-auto mb-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              AI insights temporarily unavailable
            </div>
          )}
        </div>

        {/* View Details Button */}
        {listing.url && (
          <div className="pt-4 border-t border-gray-100">
            <a
              href={listing.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold py-3 px-4 rounded-xl transition-all duration-300 transform hover:scale-[1.02] focus:ring-4 focus:ring-purple-200"
            >
              <span>View Details</span>
              <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          </div>
        )}
      </div>

      {/* Hover Effect Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-purple-600/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none rounded-2xl"></div>
    </div>
  );
};

export default PropertyCard;