import React from 'react';

interface SearchFormData {
  city: string;
  state: string;
  bedrooms: string;
  max_price: string;
  search_type: string;
  property_type: string;
}

interface SearchFormProps {
  formData: SearchFormData;
  loading: boolean;
  validationErrors?: {[key: string]: string};
  onInputChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
  onSubmit: (e: React.FormEvent) => void;
}

const SearchForm: React.FC<SearchFormProps> = ({
  formData,
  loading,
  validationErrors = {},
  onInputChange,
  onSubmit
}) => {
  return (
    <div className="relative w-full max-w-5xl mx-auto">
      <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-8 transform transition-all duration-300 hover:shadow-2xl">
        <form onSubmit={onSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* City Input */}
            <div className="group">
              <div className="relative">
                <input
                  type="text"
                  id="city"
                  name="city"
                  value={formData.city}
                  onChange={onInputChange}
                  placeholder=" "
                  className={`peer w-full px-4 py-3 text-gray-900 bg-white border-2 rounded-xl focus:ring-0 transition-all duration-200 placeholder-transparent ${
                    validationErrors.city
                      ? 'border-red-500 focus:border-red-500'
                      : 'border-gray-200 focus:border-purple-500'
                  }`}
                />
                <label
                  htmlFor="city"
                  className={`absolute left-4 -top-2.5 bg-white px-2 text-sm font-medium transition-all duration-200 peer-placeholder-shown:text-base peer-placeholder-shown:text-gray-400 peer-placeholder-shown:top-3 peer-placeholder-shown:bg-transparent peer-focus:-top-2.5 peer-focus:text-sm peer-focus:bg-white ${
                    validationErrors.city
                      ? 'text-red-600 peer-focus:text-red-600'
                      : 'text-gray-600 peer-focus:text-purple-600'
                  }`}
                >
                  City *
                </label>
                {validationErrors.city && (
                  <p className="mt-1 text-sm text-red-600 flex items-center">
                    <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    {validationErrors.city}
                  </p>
                )}
              </div>
            </div>

            {/* State Input */}
            <div className="group">
              <div className="relative">
                <input
                  type="text"
                  id="state"
                  name="state"
                  value={formData.state}
                  onChange={onInputChange}
                  placeholder=" "
                  className={`peer w-full px-4 py-3 text-gray-900 bg-white border-2 rounded-xl focus:ring-0 transition-all duration-200 placeholder-transparent ${
                    validationErrors.state
                      ? 'border-red-500 focus:border-red-500'
                      : 'border-gray-200 focus:border-purple-500'
                  }`}
                />
                <label
                  htmlFor="state"
                  className={`absolute left-4 -top-2.5 bg-white px-2 text-sm font-medium transition-all duration-200 peer-placeholder-shown:text-base peer-placeholder-shown:text-gray-400 peer-placeholder-shown:top-3 peer-placeholder-shown:bg-transparent peer-focus:-top-2.5 peer-focus:text-sm peer-focus:bg-white ${
                    validationErrors.state
                      ? 'text-red-600 peer-focus:text-red-600'
                      : 'text-gray-600 peer-focus:text-purple-600'
                  }`}
                >
                  State * (e.g., TX)
                </label>
                {validationErrors.state && (
                  <p className="mt-1 text-sm text-red-600 flex items-center">
                    <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    {validationErrors.state}
                  </p>
                )}
              </div>
            </div>

            {/* Bedrooms Select */}
            <div className="group">
              <div className="relative">
                <select
                  id="bedrooms"
                  name="bedrooms"
                  value={formData.bedrooms}
                  onChange={onInputChange}
                  className="peer w-full px-4 py-3 text-gray-900 bg-white border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:ring-0 transition-all duration-200 appearance-none cursor-pointer"
                >
                  <option value="">Any Bedrooms</option>
                  <option value="1">1 Bedroom</option>
                  <option value="2">2 Bedrooms</option>
                  <option value="3">3 Bedrooms</option>
                  <option value="4">4 Bedrooms</option>
                  <option value="5">5+ Bedrooms</option>
                </select>
                <label
                  htmlFor="bedrooms"
                  className="absolute left-4 -top-2.5 bg-white px-2 text-sm font-medium text-purple-600"
                >
                  Bedrooms
                </label>
                <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                  <svg className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Max Price Input */}
            <div className="group">
              <div className="relative">
                <input
                  type="number"
                  id="max_price"
                  name="max_price"
                  value={formData.max_price}
                  onChange={onInputChange}
                  placeholder=" "
                  className="peer w-full px-4 py-3 text-gray-900 bg-white border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:ring-0 transition-all duration-200 placeholder-transparent"
                />
                <label
                  htmlFor="max_price"
                  className="absolute left-4 -top-2.5 bg-white px-2 text-sm font-medium text-gray-600 transition-all duration-200 peer-placeholder-shown:text-base peer-placeholder-shown:text-gray-400 peer-placeholder-shown:top-3 peer-placeholder-shown:bg-transparent peer-focus:-top-2.5 peer-focus:text-sm peer-focus:text-purple-600 peer-focus:bg-white"
                >
                  Max Price {formData.search_type === 'rent' ? '(Monthly)' : '(Sale Price)'}
                </label>
              </div>
            </div>

            {/* Property Type Select */}
            <div className="group">
              <div className="relative">
                <select
                  id="property_type"
                  name="property_type"
                  value={formData.property_type}
                  onChange={onInputChange}
                  className="peer w-full px-4 py-3 text-gray-900 bg-white border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:ring-0 transition-all duration-200 appearance-none cursor-pointer"
                >
                  <option value="">Any Property Type</option>
                  <option value="apartment">Apartment</option>
                  <option value="house">House</option>
                  <option value="condo">Condo</option>
                  <option value="townhouse">Townhouse</option>
                </select>
                <label
                  htmlFor="property_type"
                  className="absolute left-4 -top-2.5 bg-white px-2 text-sm font-medium text-purple-600"
                >
                  Property Type
                </label>
                <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                  <svg className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Search Type Select */}
            <div className="group">
              <div className="relative">
                <select
                  id="search_type"
                  name="search_type"
                  value={formData.search_type}
                  onChange={onInputChange}
                  className="peer w-full px-4 py-3 text-gray-900 bg-white border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:ring-0 transition-all duration-200 appearance-none cursor-pointer"
                >
                  <option value="rent">For Rent</option>
                  <option value="buy">For Sale</option>
                </select>
                <label
                  htmlFor="search_type"
                  className="absolute left-4 -top-2.5 bg-white px-2 text-sm font-medium text-purple-600"
                >
                  Search Type
                </label>
                <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                  <svg className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-6 space-y-4">
            {/* Validation summary */}
            {Object.keys(validationErrors).length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                <div className="flex items-start">
                  <svg className="w-5 h-5 text-red-400 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <h4 className="text-sm font-medium text-red-800">Please correct the following errors:</h4>
                    <p className="text-sm text-red-700 mt-1">
                      City and State are required to search for properties.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Required fields note */}
            <p className="text-sm text-gray-600 text-center">
              <span className="text-red-500">*</span> Required fields
            </p>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold py-4 px-8 rounded-xl transition-all duration-300 transform hover:scale-[1.02] hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none focus:ring-4 focus:ring-purple-200"
            >
              <div className="flex items-center justify-center space-x-2">
                {loading ? (
                  <>
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Searching Properties...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    <span>Search Properties</span>
                  </>
                )}
              </div>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SearchForm;