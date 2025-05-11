INSERT INTO models (id, name, description, price) VALUES
(1, 'Random Forest', 'Модель на основе случайного леса для прогнозирования цены Bitcoin. Высокая точность, средняя скорость.', 10.0),
(2, 'XGBoost', 'Модель на основе градиентного бустинга для прогнозирования цены Bitcoin. Высокая точность, быстрое обучение.', 15.0),
(3, 'LightGBM', 'Легковесная модель градиентного бустинга для прогнозирования цены Bitcoin. Быстрая и эффективная.', 12.0),
(4, 'Prophet', 'Модель временных рядов от Facebook для прогнозирования цены Bitcoin. Хорошо работает с сезонными данными.', 20.0)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    price = EXCLUDED.price;
