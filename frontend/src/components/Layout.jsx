import React from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogOut, Film, Home, Shield, User } from 'lucide-react';
import { motion } from 'framer-motion';

const Layout = () => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="navbar-brand">
          <Film size={28} />
          <span>MNL Project</span>
        </div>

        <div className="navbar-menu">
          <motion.button
            className="nav-link"
            onClick={() => navigate(isAdmin() ? '/admin' : '/dashboard')}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Home size={18} />
            Dashboard
          </motion.button>

          <div className="navbar-user">
            <div className="user-info">
              <div className="user-avatar-small">
                {user?.username?.charAt(0).toUpperCase()}
              </div>
              <div className="user-details">
                <span className="user-name">{user?.username}</span>
                <span className="user-role">
                  {isAdmin() ? (
                    <>
                      <Shield size={12} />
                      Admin
                    </>
                  ) : (
                    <>
                      <User size={12} />
                      User
                    </>
                  )}
                </span>
              </div>
            </div>

            <motion.button
              className="logout-button"
              onClick={handleLogout}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <LogOut size={18} />
              Logout
            </motion.button>
          </div>
        </div>
      </nav>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
