import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import CVDetail from "./pages/CVDetail";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/cv/:id" element={<CVDetail />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
