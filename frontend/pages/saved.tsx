import React, { useState, useEffect } from 'react';
import PropertyCard from '@/components/PropertyCard';

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
  url?: string;
  description?: string;
  photo_url?: string;
  photos?: string[];
}

const SavedPropertiesPage: React.FC = () => {
  const [savedListings, setSavedListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load saved properties from localStorage
    const loadSavedProperties = () => {
      try {
        const saved = localStorage.getItem('savedProperties');
        if (saved) {
          const parsedSaved = JSON.parse(saved);
          setSavedListings(parsedSaved);
        }
      } catch (error) {
        console.error('Error loading saved properties:', error);
      } finally {
        setLoading(false);
      }
    };

    loadSavedProperties();
  }, []);

  const removeSavedProperty = (propertyId: number) => {
    const updatedListings = savedListings.filter(listing => listing.id !== propertyId);
    setSavedListings(updatedListings);
    localStorage.setItem('savedProperties', JSON.stringify(updatedListings));
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading saved properties...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Saved Properties
          </h1>
          <p className="text-xl text-gray-600">
            Properties you've bookmarked for later review
          </p>
        </div>

        {savedListings.length === 0 ? (
          // Empty State
          <div className="text-center py-16">
            <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
            </div>
            <h3 className="text-2xl font-semibold text-gray-900 mb-4">No Saved Properties</h3>
            <p className="text-gray-600 mb-8 max-w-md mx-auto">
              You haven't saved any properties yet. Browse our listings and save the ones you're interested in.
            </p>
            <a
              href="/"
              className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-xl hover:from-purple-700 hover:to-blue-700 transition-all duration-200 transform hover:scale-105"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Browse Properties
            </a>
          </div>
        ) : (
          // Saved Properties Grid
          <>
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <p className="text-lg text-gray-600">
                  <span className="font-semibold text-purple-600">{savedListings.length}</span> saved {savedListings.length === 1 ? 'property' : 'properties'}
                </p>
                <button
                  onClick={() => {
                    if (confirm('Are you sure you want to clear all saved properties?')) {
                      setSavedListings([]);
                      localStorage.removeItem('savedProperties');
                    }
                  }}
                  className="text-sm text-red-600 hover:text-red-700 font-medium"
                >
                  Clear All
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {savedListings.map((listing) => (
                <div key={listing.id} className="relative">
                  <PropertyCard
                    listing={listing}
                    searchType="rent" // Default to rent, could be improved with actual search type
                    formatPrice={formatPrice}
                  />

                  {/* Remove from Saved Button */}
                  <button
                    onClick={() => removeSavedProperty(listing.id)}
                    className="absolute top-4 left-4 z-20 w-8 h-8 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center transition-colors duration-200"
                    title="Remove from saved"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default SavedPropertiesPage;