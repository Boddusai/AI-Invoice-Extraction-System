import {
  Route,
  Routes,
} from "react-router-dom";

import Sidebar from "./components/Sidebar";

import Dashboard from "./pages/Dashboard";
import Invoices from "./pages/Invoices";
import ReviewInvoice from "./pages/ReviewInvoice";
import UploadInvoice from "./pages/UploadInvoice";


function App() {
  return (
    <div className="app-layout">

      <Sidebar />

      <main className="main-content">

        <Routes>

          <Route
            path="/"
            element={<Dashboard />}
          />

          <Route
            path="/upload"
            element={<UploadInvoice />}
          />

          <Route
            path="/invoices"
            element={<Invoices />}
          />

          <Route
            path="/review"
            element={<ReviewInvoice />}
          />

          <Route
            path="/review/:invoiceId"
            element={<ReviewInvoice />}
          />

        </Routes>

      </main>

    </div>
  );
}

export default App;