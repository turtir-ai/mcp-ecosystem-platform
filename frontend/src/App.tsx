import { CssBaseline } from '@mui/material';
import { ThemeProvider } from '@mui/material/styles';
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import { SWRConfig } from 'swr';

import Layout from './components/Layout/Layout';
import theme from './theme/theme';

// Import pages
import Dashboard from './pages/Dashboard/Dashboard';
import MCPServers from './pages/MCPServers/MCPServers';
import Workflows from './pages/Workflows/Workflows';

// Placeholder pages (we'll create these next)
const NetworkMonitoring = () => <div>Network Monitoring Page</div>;
const Security = () => <div>Security Page</div>;
const Research = () => <div>Research Page</div>;
const Privacy = () => <div>Privacy Page</div>;
const Settings = () => <div>Settings Page</div>;

function App() {
  return (
    <SWRConfig
      value={{
        fetcher: async (url: string) => {
          // Use our API client's request method
          const response = await fetch(`/api${url}`);
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        },
        refreshInterval: 30000, // Refresh every 30 seconds
        revalidateOnFocus: false,
        errorRetryCount: 2,
        onError: (error) => {
          console.error('SWR Error:', error);
        },
      }}
    >
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/mcp-servers" element={<MCPServers />} />
              <Route path="/network" element={<NetworkMonitoring />} />
              <Route path="/security" element={<Security />} />
              <Route path="/workflows" element={<Workflows />} />
              <Route path="/research" element={<Research />} />
              <Route path="/privacy" element={<Privacy />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Layout>
        </Router>
      </ThemeProvider>
    </SWRConfig>
  );
}

export default App;