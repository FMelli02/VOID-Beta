// En frontend/src/App.jsx

import { useState, useEffect } from 'react';
import './App.css'; // Dejamos los estilos básicos

function App() {
  // Estados para guardar los productos, saber si está cargando o si hubo un error.
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // useEffect se ejecuta cuando el componente carga por primera vez.
  // Es el lugar ideal para llamar a nuestra API.
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        // ¡LA LLAMADA CLAVE! Apuntamos al endpoint de productos de nuestro backend.
        // Asegurate de que el puerto (8000) sea el correcto.
        const response = await fetch('http://127.0.0.1:8000/api/products/');
        
        if (!response.ok) {
          throw new Error('La respuesta del servidor no fue buena, ¡rajemos!');
        }

        const data = await response.json();
        setProducts(data); // ¡Éxito! Guardamos los productos.
      } catch (error) {
        setError(error.message); // ¡Falló! Guardamos el mensaje de error.
      } finally {
        setLoading(false); // Terminó la carga (para bien o para mal).
      }
    };

    fetchProducts(); // Ejecutamos la función que acabamos de crear.
  }, []); // El `[]` vacío asegura que esto se ejecute solo una vez.

  // Mostramos un mensaje mientras carga.
  if (loading) return <div>Cargando productos, bancame un toque...</div>;
  
  // Mostramos un mensaje si algo se rompió.
  if (error) return <div>¡Uh, se rompió todo! Error: {error}</div>;

  // Si todo salió bien, mostramos los productos.
  return (
    <div className="App">
      <h1>¡Mi Tienda de Pilcha!</h1>
      <div className="product-list">
        {/* Usamos .map() para crear un bloque HTML por cada producto */}
        {products.map(product => (
          <div key={product.id} className="product-card">
            <h2>{product.nombre}</h2>
            <p>{product.descripcion}</p>
            <p><strong>Precio: ${product.precio}</strong></p>
            <p>Stock: {product.stock}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
