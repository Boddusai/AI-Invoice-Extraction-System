import {
    FileText,
    LayoutDashboard,
    Upload,
    List,
    SearchCheck,
  } from "lucide-react";
  
  import { NavLink } from "react-router-dom";
  
  
  function Sidebar() {
    const menuItems = [
      {
        name: "Dashboard",
        path: "/",
        icon: LayoutDashboard,
      },
      {
        name: "Upload Invoice",
        path: "/upload",
        icon: Upload,
      },
      {
        name: "Invoices",
        path: "/invoices",
        icon: List,
      },
      {
        name: "Review",
        path: "/review",
        icon: SearchCheck,
      },
    ];
  
    return (
      <aside className="sidebar">
  
        <div className="brand">
          <div className="brand-icon">
            <FileText size={26} />
          </div>
  
          <div>
            <h2>InvoiceAI</h2>
            <span>Smart Extraction</span>
          </div>
        </div>
  
        <nav className="sidebar-menu">
  
          {menuItems.map((item) => {
            const Icon = item.icon;
  
            return (
              <NavLink
                key={item.name}
                to={item.path}
                className={({ isActive }) =>
                  isActive
                    ? "menu-item active"
                    : "menu-item"
                }
              >
                <Icon size={19} />
  
                <span>
                  {item.name}
                </span>
              </NavLink>
            );
          })}
  
        </nav>
  
        <div className="sidebar-footer">
          <p>AI Invoice System</p>
          <span>Prototype v1.0</span>
        </div>
  
      </aside>
    );
  }
  
  export default Sidebar;