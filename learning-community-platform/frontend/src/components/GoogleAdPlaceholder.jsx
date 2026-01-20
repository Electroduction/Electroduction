import { XMarkIcon } from '@heroicons/react/24/outline';
import { useState } from 'react';

const GoogleAdPlaceholder = ({ slot }) => {
  const [isVisible, setIsVisible] = useState(true);

  if (!isVisible) return null;

  return (
    <div className="relative bg-gray-100 dark:bg-gray-800 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8">
      <button
        onClick={() => setIsVisible(false)}
        className="absolute top-2 right-2 p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700"
        aria-label="Close ad"
      >
        <XMarkIcon className="h-5 w-5 text-gray-500" />
      </button>
      <div className="text-center space-y-2">
        <div className="text-sm text-gray-500 dark:text-gray-400">Advertisement</div>
        <div className="text-lg font-medium text-gray-700 dark:text-gray-300">
          Google Ad Space ({slot})
        </div>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          This area will display Google AdSense ads
        </div>
      </div>
    </div>
  );
};

export default GoogleAdPlaceholder;
