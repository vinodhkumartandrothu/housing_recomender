import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import axios from 'axios';
import SearchForm from '@/components/SearchForm';
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

interface SearchFormData {
  city: string;
  state: string;
  bedrooms: string;
  max_price: string;
  search_type: string;
  property_type: string;
}

const HomePage: React.FC = () => {
  const router = useRouter();

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
  const [sortBy, setSortBy] = useState<string>('relevance');
  const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({});

  // Load search parameters from URL on page load
  useEffect(() => {
    const { query } = router;

    if (query.city || query.state || query.bedrooms || query.max_price || query.search_type || query.property_type) {
      const urlFormData: SearchFormData = {
        city: (query.city as string) || '',
        state: (query.state as string) || '',
        bedrooms: (query.bedrooms as string) || '',
        max_price: (query.max_price as string) || '',
        search_type: (query.search_type as string) || 'rent',
        property_type: (query.property_type as string) || ''
      };

      setFormData(urlFormData);

      // Automatically perform search if URL has parameters
      performSearch(urlFormData);
    }
  }, [router.query]);

  // Update URL when form data changes (for browser back/forward)
  const updateURL = (searchData: SearchFormData) => {
    const params = new URLSearchParams();

    Object.entries(searchData).forEach(([key, value]) => {
      if (value && value !== '') {
        params.set(key, value);
      }
    });

    const queryString = params.toString();
    const newUrl = queryString ? `/?${queryString}` : '/';

    router.replace(newUrl, undefined, { shallow: true });
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear validation error when user starts typing
    if (validationErrors[name]) {
      setValidationErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  // Validate required fields
  const validateForm = (): boolean => {
    const errors: {[key: string]: string} = {};

    // City is required
    if (!formData.city.trim()) {
      errors.city = 'Please enter a city';
    }

    // State is required
    if (!formData.state.trim()) {
      errors.state = 'Please enter a state';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Separate function to perform the actual search
  const performSearch = async (searchData: SearchFormData) => {
    setLoading(true);
    setError('');

    try {
      // Build query parameters
      const params = new URLSearchParams();

      if (searchData.city) params.append('city', searchData.city);
      if (searchData.state) params.append('state_code', searchData.state);
      if (searchData.bedrooms) params.append('bedrooms', searchData.bedrooms);
      if (searchData.max_price) params.append('max_price', searchData.max_price);
      if (searchData.search_type) params.append('search_type', searchData.search_type);
      if (searchData.property_type) params.append('property_type', searchData.property_type);

      const response = await axios.get(
        `http://127.0.0.1:8000/api/v1/search?${params.toString()}`
      );

      setListings(response.data.listings || response.data);
    } catch (err) {
      console.error('Search error:', err);
      setError('Failed to search listings. Please make sure your backend is running on http://127.0.0.1:8000');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Clear any previous API errors
    setError('');

    // Validate form before proceeding
    if (!validateForm()) {
      return; // Don't proceed if validation fails
    }

    // Update URL with search parameters
    updateURL(formData);

    // Perform search with current form data
    await performSearch(formData);
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const sortListings = (listings: Listing[], sortBy: string) => {
    const sorted = [...listings];
    switch (sortBy) {
      case 'price-low':
        return sorted.sort((a, b) => (a.price || 0) - (b.price || 0));
      case 'price-high':
        return sorted.sort((a, b) => (b.price || 0) - (a.price || 0));
      case 'bedrooms':
        return sorted.sort((a, b) => b.bedrooms - a.bedrooms);
      case 'sqft':
        return sorted.sort((a, b) => b.square_feet - a.square_feet);
      case 'relevance':
      default:
        return sorted;
    }
  };

  const sortedListings = sortListings(listings, sortBy);

  return (
    <div className="relative">
      {/* Hero Section with Background */}
      <div className="relative overflow-hidden">
        {/* Background with gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/90 via-purple-900/80 to-blue-900/90"></div>
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0 bg-repeat" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Cpath d='M20 20c0 11.046-8.954 20-20 20v20h40V20H20z'/%3E%3C/g%3E%3C/svg%3E")`
          }}></div>
        </div>

        <div className="relative px-4 py-24 sm:px-6 lg:px-8 lg:py-32">
          <div className="text-center max-w-5xl mx-auto">
            <div className="mb-8">
              <h1 className="text-5xl md:text-7xl lg:text-8xl font-black mb-6 leading-tight">
                <span className="bg-gradient-to-r from-white via-blue-100 to-indigo-200 bg-clip-text text-transparent">
                  Find Your Perfect
                </span>
                <br />
                <span className="bg-gradient-to-r from-blue-200 via-indigo-200 to-purple-200 bg-clip-text text-transparent">
                  Home
                </span>
              </h1>

              {/* Enhanced Tagline */}
              <p className="text-xl md:text-2xl lg:text-3xl text-blue-100 mb-4 max-w-4xl mx-auto leading-relaxed font-light">
                AI-powered housing search with smart recommendations
              </p>
              <p className="text-lg md:text-xl text-blue-200 mb-12 max-w-3xl mx-auto leading-relaxed font-light">
                tailored to your lifestyle and preferences
              </p>
            </div>

            {/* Enhanced Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-16">
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20 hover:bg-white/15 transition-all duration-300 group">
                <div className="flex items-center justify-center mb-3">
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-400 to-blue-400 rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                  </div>
                </div>
                <div className="text-3xl md:text-4xl font-bold text-white mb-2 group-hover:scale-105 transition-transform duration-300">10K+</div>
                <div className="text-sm text-blue-200 font-medium uppercase tracking-wide">Properties</div>
              </div>

              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20 hover:bg-white/15 transition-all duration-300 group">
                <div className="flex items-center justify-center mb-3">
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-400 to-indigo-400 rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                </div>
                <div className="text-3xl md:text-4xl font-bold text-white mb-2 group-hover:scale-105 transition-transform duration-300">AI</div>
                <div className="text-sm text-blue-200 font-medium uppercase tracking-wide">Powered</div>
              </div>

              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20 hover:bg-white/15 transition-all duration-300 group">
                <div className="flex items-center justify-center mb-3">
                  <div className="w-12 h-12 bg-gradient-to-r from-indigo-400 to-purple-400 rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
                <div className="text-3xl md:text-4xl font-bold text-white mb-2 group-hover:scale-105 transition-transform duration-300">24/7</div>
                <div className="text-sm text-blue-200 font-medium uppercase tracking-wide">Available</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Search Form Section */}
      <div className="relative -mt-20 px-4 sm:px-6 lg:px-8 pb-16">
        <SearchForm
          formData={formData}
          loading={loading}
          validationErrors={validationErrors}
          onInputChange={handleInputChange}
          onSubmit={handleSubmit}
        />
      </div>

      {/* Error Message */}
      {error && (
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 mb-12">
          <div className="bg-red-50 border-l-4 border-red-400 rounded-xl p-6 shadow-lg">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-red-800">{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Results Section */}
      {listings.length > 0 && (
        <div className="px-4 sm:px-6 lg:px-8 pb-20">
          <div className="max-w-7xl mx-auto">
            {/* Results Header */}
            <div className="text-center mb-8">
              <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                Search Results
              </h2>
              <p className="text-xl text-gray-600">
                <span className="font-semibold text-purple-600">{listings.length}</span> properties found matching your criteria
              </p>
            </div>

            {/* Sorting Toolbar */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 p-4 bg-white/60 backdrop-blur-sm rounded-2xl border border-gray-200/50 shadow-sm">
              <div className="flex items-center space-x-4 mb-4 sm:mb-0">
                <h3 className="text-lg font-semibold text-gray-900">
                  {listings.length} {listings.length === 1 ? 'Property' : 'Properties'}
                </h3>
              </div>

              <div className="flex items-center space-x-3">
                <label htmlFor="sort" className="text-sm font-medium text-gray-700">
                  Sort by:
                </label>
                <select
                  id="sort"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-white border border-gray-300 rounded-xl px-4 py-2 text-sm font-medium text-gray-700 focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 hover:border-purple-300"
                >
                  <option value="relevance">Relevance</option>
                  <option value="price-low">Price: Low to High</option>
                  <option value="price-high">Price: High to Low</option>
                  <option value="bedrooms">Most Bedrooms</option>
                  <option value="sqft">Largest First</option>
                </select>
              </div>
            </div>

            {/* Property Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {sortedListings.map((listing) => (
                <PropertyCard
                  key={listing.id}
                  listing={listing}
                  searchType={formData.search_type}
                  formatPrice={formatPrice}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* No Results */}
      {!loading && listings.length === 0 && formData.city && (
        <div className="px-4 sm:px-6 lg:px-8 pb-20">
          <div className="max-w-2xl mx-auto text-center">
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-12 shadow-xl border border-gray-100">
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-10 h-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">No Properties Found</h3>
              <p className="text-gray-600 mb-8 leading-relaxed">
                We couldn't find any properties matching your search criteria. Try adjusting your filters or exploring a different location.
              </p>
              <div className="space-y-2 text-sm text-gray-500">
                <p>• Try expanding your price range</p>
                <p>• Consider nearby cities or neighborhoods</p>
                <p>• Adjust bedroom or property type requirements</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;