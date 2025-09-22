import React, { useState } from 'react';
import axios from 'axios';

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
}

interface SearchFormData {
  city: string;
  state: string;
  bedrooms: string;
  max_price: string;
  search_type: string;
  property_type: string;
}

const HomePage: React.FC = () => {
  const [formData, setFormData] = useState<SearchFormData>({
    city: '',
    state: '',
    bedrooms: '',
    max_price: '',
    search_type: 'rent',
    property_type: ''
  });

  const [listings, setListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Build query parameters
      const params = new URLSearchParams();

      if (formData.city) params.append('city', formData.city);
      if (formData.state) params.append('state_code', formData.state);  // 👈 FIXED
      if (formData.bedrooms) params.append('bedrooms', formData.bedrooms);
      if (formData.max_price) params.append('max_price', formData.max_price);
      if (formData.search_type) params.append('search_type', formData.search_type);
      if (formData.property_type) params.append('property_type', formData.property_type);

      const response = await axios.get(
        `http://127.0.0.1:8000/api/v1/search?${params.toString()}`
      );

      // setListings(response.data);
      setListings(response.data.listings || response.data);
    } catch (err) {
      console.error('Search error:', err);
      setError('Failed to search listings. Please make sure your backend is running on http://127.0.0.1:8000');
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Find Your Perfect Home
        </h1>
        <p className="text-xl text-gray-600">
          AI-powered housing search with smart recommendations
        </p>
      </div>

      {/* Search Form */}
      <div className="card max-w-4xl mx-auto">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Search Properties</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-1">
                City
              </label>
              <input
                type="text"
                id="city"
                name="city"
                value={formData.city}
                onChange={handleInputChange}
                placeholder="e.g., Dallas"
                className="input-field w-full"
              />
            </div>

            <div>
              <label htmlFor="state" className="block text-sm font-medium text-gray-700 mb-1">
                State
              </label>
              <input
                type="text"
                id="state"
                name="state"
                value={formData.state}
                onChange={handleInputChange}
                placeholder="e.g., TX"
                className="input-field w-full"
              />
            </div>

            <div>
              <label htmlFor="search_type" className="block text-sm font-medium text-gray-700 mb-1">
                Search Type
              </label>
              <select
                id="search_type"
                name="search_type"
                value={formData.search_type}
                onChange={handleInputChange}
                className="input-field w-full"
              >
                <option value="rent">For Rent</option>
                <option value="buy">For Sale</option>
              </select>
            </div>

            <div>
              <label htmlFor="bedrooms" className="block text-sm font-medium text-gray-700 mb-1">
                Bedrooms
              </label>
              <select
                id="bedrooms"
                name="bedrooms"
                value={formData.bedrooms}
                onChange={handleInputChange}
                className="input-field w-full"
              >
                <option value="">Any</option>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4</option>
                <option value="5">5+</option>
              </select>
            </div>

            <div>
              <label htmlFor="max_price" className="block text-sm font-medium text-gray-700 mb-1">
                Max Price {formData.search_type === 'rent' ? '(Monthly)' : '(Sale Price)'}
              </label>
              <input
                type="number"
                id="max_price"
                name="max_price"
                value={formData.max_price}
                onChange={handleInputChange}
                placeholder={formData.search_type === 'rent' ? 'e.g., 2500' : 'e.g., 400000'}
                className="input-field w-full"
              />
            </div>

            <div>
              <label htmlFor="property_type" className="block text-sm font-medium text-gray-700 mb-1">
                Property Type
              </label>
              <select
                id="property_type"
                name="property_type"
                value={formData.property_type}
                onChange={handleInputChange}
                className="input-field w-full"
              >
                <option value="">Any</option>
                <option value="apartment">Apartment</option>
                <option value="house">House</option>
                <option value="condo">Condo</option>
                <option value="townhouse">Townhouse</option>
              </select>
            </div>
          </div>

          <div className="pt-4">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full md:w-auto px-8 py-3 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Searching...' : 'Search Properties'}
            </button>
          </div>
        </form>
      </div>

      {/* Error Message */}
      {error && (
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex">
              <div className="text-red-400">
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {listings.length > 0 && (
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">
            Search Results ({listings.length} properties found)
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {listings.map((listing) => (
              <div key={listing.id} className="card hover:shadow-lg transition-shadow duration-200">
                <div className="space-y-3">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
                      {listing.title}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {listing.city}, {listing.state}
                    </p>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-2xl font-bold text-primary-600">
                      {listing.price_range
                        ? listing.price_range
                        : listing.price && listing.price > 0
                        ? `${formatPrice(listing.price)}${formData.search_type === 'rent' ? '/mo' : ''}`
                        : "Contact for pricing"
                      }
                    </span>
                    {listing.square_feet && (
                      <span className="text-sm text-gray-500">
                        {listing.square_feet.toLocaleString()} sq ft
                      </span>
                    )}
                  </div>

                  <div className="flex space-x-4 text-sm text-gray-600">
                    <span className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
                      </svg>
                      {listing.bedrooms} bed
                    </span>
                    <span className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M10 3v4h4V3z" />
                      </svg>
                      {listing.bathrooms} bath
                    </span>
                  </div>

                  {listing.description && (
                    <p className="text-sm text-gray-600 line-clamp-3">
                      {listing.description}
                    </p>
                  )}

                  {listing.url && (
                    <div className="pt-2">
                      <a
                        href={listing.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center text-primary-600 hover:text-primary-700 text-sm font-medium"
                      >
                        View Details
                        <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {!loading && listings.length === 0 && formData.city && (
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-gray-50 rounded-lg p-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No properties found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Try adjusting your search criteria or check a different location.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;