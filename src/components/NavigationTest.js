import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";

const NavigationTest = () => {
  const navigate = useNavigate();

  const testNavigation = (path) => {
    console.log(`🧭 Testing navigation to: ${path}`);
    try {
      navigate(path);
      console.log(`✅ Navigation command executed for: ${path}`);
    } catch (error) {
      console.error(`❌ Navigation failed for ${path}:`, error);
    }
  };

  return (
    <div style={{ 
      padding: '20px', 
      margin: '20px', 
      border: '2px solid #8b5cf6', 
      borderRadius: '8px',
      backgroundColor: '#f0f9ff'
    }}>
      <h3>🧭 Navigation Test</h3>
      <p style={{ fontSize: '14px', color: '#666', marginBottom: '15px' }}>
        Test if React Router navigation is working properly
      </p>
      
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <Button onClick={() => testNavigation('/dashboard')}>
          Test Dashboard Navigation
        </Button>
        <Button onClick={() => testNavigation('/profile')}>
          Test Profile Navigation  
        </Button>
        <Button onClick={() => testNavigation('/nonexistent')}>
          Test Invalid Route
        </Button>
        <Button onClick={() => testNavigation('/')}>
          Test Home Navigation
        </Button>
      </div>
      
      <p style={{ fontSize: '12px', color: '#666', marginTop: '15px' }}>
        Click buttons and check browser console for navigation results
      </p>
    </div>
  );
};

export default NavigationTest;
