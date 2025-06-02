import os
from dotenv import load_dotenv
from .github_integration import GitHubPRCreator

def create_mvp_pr():
    """Create a PR with the MVP implementation"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get GitHub token and repo
        github_token = os.getenv("GITHUB_TOKEN")
        github_repo = os.getenv("GITHUB_REPO", "antonioalamo/buuks")
        
        if not github_token:
            print("❌ Error: GITHUB_TOKEN not found in environment variables")
            return False
            
        print(f"\nCreating MVP Pull Request")
        print(f"Repository: {github_repo}")
        
        # Initialize PR creator
        pr_creator = GitHubPRCreator(github_repo)
        
        # Define file changes
        file_changes = {
            # Frontend structure
            "frontend/package.json": """{
  "name": "buuks",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.17.0",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^13.5.0",
    "@types/jest": "^27.5.2",
    "@types/node": "^16.18.91",
    "@types/react": "^18.2.67",
    "@types/react-dom": "^18.2.22",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.3",
    "react-scripts": "5.0.1",
    "recharts": "^2.12.2",
    "typescript": "^4.9.5",
    "web-vitals": "^2.1.4",
    "tailwindcss": "^3.4.1",
    "postcss": "^8.4.35",
    "autoprefixer": "^10.4.18"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}""",
            "frontend/tsconfig.json": """{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"]
}""",
            "frontend/tailwind.config.js": """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
}""",
            "frontend/postcss.config.js": """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}""",
            "frontend/src/index.tsx": """import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles/index.css';
import App from './App';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);""",
            "frontend/src/styles/index.css": """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-gray-50;
}""",
            "frontend/src/App.tsx": """import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import Configuration from './components/Configuration';
import Database from './components/Database';

const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/configuration" element={<Configuration />} />
            <Route path="/database" element={<Database />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default App;""",
            "frontend/src/components/Navbar.tsx": """import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navbar: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white';
  };

  return (
    <nav className="bg-gray-800">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <span className="text-white text-xl font-bold">Buuks</span>
            </div>
            <div className="ml-10 flex items-baseline space-x-4">
              <Link
                to="/"
                className={`${isActive('/')} rounded-md px-3 py-2 text-sm font-medium`}
              >
                Dashboard
              </Link>
              <Link
                to="/configuration"
                className={`${isActive('/configuration')} rounded-md px-3 py-2 text-sm font-medium`}
              >
                Configuration
              </Link>
              <Link
                to="/database"
                className={`${isActive('/database')} rounded-md px-3 py-2 text-sm font-medium`}
              >
                Database
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;""",
            "frontend/src/components/Dashboard.tsx": """import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { sampleData } from '../data/sampleData';

const Dashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
        <div className="h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={sampleData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="revenue" stackId="a" fill="#8884d8" name="Revenue" />
              <Bar dataKey="expenses" stackId="a" fill="#82ca9d" name="Expenses" />
              <Bar dataKey="profit" stackId="a" fill="#ffc658" name="Profit" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;""",
            "frontend/src/components/Configuration.tsx": """import React from 'react';

const Configuration: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h1 className="text-2xl font-bold mb-4">Configuration</h1>
      <p className="text-gray-600">
        This page will allow you to configure dashboard charts and settings.
        Coming soon in the next iteration!
      </p>
    </div>
  );
};

export default Configuration;""",
            "frontend/src/components/Database.tsx": """import React from 'react';
import { sampleData } from '../data/sampleData';

const Database: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h1 className="text-2xl font-bold mb-4">Database</h1>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Month</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Revenue</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Expenses</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Profit</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sampleData.map((item, index) => (
              <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.revenue}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.expenses}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.profit}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Database;""",
            "frontend/src/data/sampleData.ts": """export const sampleData = [
  {
    name: 'Jan',
    revenue: 4000,
    expenses: 2400,
    profit: 1600
  },
  {
    name: 'Feb',
    revenue: 3000,
    expenses: 1398,
    profit: 1602
  },
  {
    name: 'Mar',
    revenue: 2000,
    expenses: 1800,
    profit: 200
  },
  {
    name: 'Apr',
    revenue: 2780,
    expenses: 2908,
    profit: -128
  },
  {
    name: 'May',
    revenue: 1890,
    expenses: 1800,
    profit: 90
  },
  {
    name: 'Jun',
    revenue: 2390,
    expenses: 1800,
    profit: 590
  },
];""",
            "README.md": """# Buuks

A modern financial dashboard application built with React, TypeScript, and Tailwind CSS.

## Features

- 📊 Interactive Dashboard with stacked bar charts
- ⚙️ Configuration page for customizing dashboard
- 📋 Database view for raw data inspection
- 🎨 Modern UI with Tailwind CSS
- 📱 Fully responsive design

## Tech Stack

- React 18
- TypeScript
- React Router for navigation
- Recharts for data visualization
- Tailwind CSS for styling

## Getting Started

1. Clone the repository
2. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
3. Start the development server:
   ```bash
   npm start
   ```

## Project Structure

```
frontend/
├── src/
│   ├── components/     # React components
│   ├── data/          # Sample data
│   ├── styles/        # CSS styles
│   ├── App.tsx        # Main app component
│   └── index.tsx      # Entry point
└── public/            # Static assets
```

## Development

- `npm start` - Start development server
- `npm test` - Run tests
- `npm run build` - Build for production

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT""",
            ".gitignore": """# Dependencies
node_modules/
/.pnp
.pnp.js

# Testing
/coverage

# Production
/build

# Misc
.DS_Store
.env.local
.env.development.local
.env.test.local
.env.production.local

npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
venv/
ENV/"""
        }
        
        # Create a test PR
        try:
            pr_url = pr_creator.create_pull_request(
                branch_name="feat/mvp-implementation",
                title="feat: Add MVP Implementation",
                description="""# MVP Implementation

This PR adds the initial MVP implementation with the following features:

## Frontend
- Modern React application with TypeScript
- Responsive layout with horizontal navigation
- Three main routes: Dashboard, Configuration, Database
- Sample stacked bar chart using Recharts
- Clean UI using Tailwind CSS
- Sample data implementation

## Features
- 📊 Interactive Dashboard with financial data visualization
- ⚙️ Configuration page (placeholder for future implementation)
- 📋 Database view showing raw data in a table
- 🎨 Modern and responsive design
- 🚀 Production-ready setup

## Technical Details
- React 18 with TypeScript
- React Router for navigation
- Recharts for data visualization
- Tailwind CSS for styling
- Sample data structure for demonstration

## Next Steps
- [ ] Add backend API integration
- [ ] Implement configuration functionality
- [ ] Add more chart types
- [ ] Implement data management features
- [ ] Add authentication

Please review the implementation and provide feedback on the structure and approach.""",
                file_changes=file_changes
            )
            print("\n✅ Success! Pull request created:")
            print(f"PR URL: {pr_url}")
            return True
            
        except Exception as e:
            print(f"\n❌ Error creating pull request: {str(e)}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    create_mvp_pr() 