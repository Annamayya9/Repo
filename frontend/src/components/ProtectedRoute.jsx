import { useAuth } from '../contexts/AuthContext';
import LoginScreen from './LoginScreen';

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  return children;
}

export default ProtectedRoute;