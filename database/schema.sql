-- Smart AI-Based Grocery List Optimiser — MySQL schema
-- Generated from the SQLAlchemy models (backend/app/models). Alternative to 'flask db upgrade'.
-- Usage (PowerShell): Get-Content database\schema.sql | mysql -u grocery_user -p smart_grocery

SET FOREIGN_KEY_CHECKS = 0;
CREATE TABLE IF NOT EXISTS `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS `households` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `household_name` varchar(120) NOT NULL,
  `family_size` int(11) NOT NULL,
  `shopping_frequency` varchar(20) NOT NULL,
  `monthly_budget` decimal(12,2) NOT NULL,
  `planning_period_days` int(11) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `households_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS `grocery_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `household_id` int(11) NOT NULL,
  `name` varchar(120) NOT NULL,
  `category` varchar(50) NOT NULL,
  `unit` varchar(20) NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  `priority` varchar(20) NOT NULL,
  `description` varchar(500) DEFAULT NULL,
  `initial_monthly_estimate` decimal(12,3) DEFAULT NULL,
  `is_archived` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_item_household_name` (`household_id`,`name`),
  KEY `ix_grocery_items_household_id` (`household_id`),
  CONSTRAINT `grocery_items_ibfk_1` FOREIGN KEY (`household_id`) REFERENCES `households` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS `inventory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `household_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `quantity` decimal(12,3) NOT NULL,
  `low_stock_threshold` decimal(12,3) NOT NULL,
  `expiry_date` date DEFAULT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `item_id` (`item_id`),
  KEY `ix_inventory_household_id` (`household_id`),
  CONSTRAINT `inventory_ibfk_1` FOREIGN KEY (`household_id`) REFERENCES `households` (`id`) ON DELETE CASCADE,
  CONSTRAINT `inventory_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `grocery_items` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ck_inventory_quantity_non_negative` CHECK (`quantity` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS `stock_movements` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `household_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `change_quantity` decimal(12,3) NOT NULL,
  `reason` varchar(40) NOT NULL,
  `reference_type` varchar(30) DEFAULT NULL,
  `reference_id` int(11) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_stock_movements_household_id` (`household_id`),
  KEY `ix_stock_movements_item_id` (`item_id`),
  CONSTRAINT `stock_movements_ibfk_1` FOREIGN KEY (`household_id`) REFERENCES `households` (`id`) ON DELETE CASCADE,
  CONSTRAINT `stock_movements_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `grocery_items` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS `recommendations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `household_id` int(11) NOT NULL,
  `planning_period_start` date NOT NULL,
  `planning_period_end` date NOT NULL,
  `predicted_total_cost` decimal(12,2) NOT NULL,
  `final_total_cost` decimal(12,2) NOT NULL,
  `budget` decimal(12,2) NOT NULL,
  `prediction_method` varchar(120) NOT NULL,
  `history_periods` int(11) NOT NULL,
  `status` varchar(20) NOT NULL,
  `budget_status` varchar(30) NOT NULL,
  `explanation` text DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_recommendations_household_id` (`household_id`),
  CONSTRAINT `recommendations_ibfk_1` FOREIGN KEY (`household_id`) REFERENCES `households` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS `recommendation_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `recommendation_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `predicted_quantity` decimal(12,3) NOT NULL,
  `stock_quantity` decimal(12,3) NOT NULL,
  `recommended_quantity` decimal(12,3) NOT NULL,
  `final_quantity` decimal(12,3) NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  `estimated_cost` decimal(12,2) NOT NULL,
  `priority` varchar(20) NOT NULL,
  `prediction_source` varchar(30) NOT NULL,
  `periods_used` int(11) NOT NULL,
  `data_sufficiency` varchar(20) NOT NULL,
  `reason` varchar(500) DEFAULT NULL,
  `plan_status` varchar(20) NOT NULL,
  `adjustment_note` varchar(500) DEFAULT NULL,
  `is_checked` tinyint(1) NOT NULL,
  `is_purchased` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_recommendation_item` (`recommendation_id`,`item_id`),
  KEY `item_id` (`item_id`),
  KEY `ix_recommendation_items_recommendation_id` (`recommendation_id`),
  CONSTRAINT `recommendation_items_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `grocery_items` (`id`),
  CONSTRAINT `recommendation_items_ibfk_2` FOREIGN KEY (`recommendation_id`) REFERENCES `recommendations` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS `purchases` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `household_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `quantity` decimal(12,3) NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  `total_price` decimal(12,2) NOT NULL,
  `purchase_date` date NOT NULL,
  `store_name` varchar(120) DEFAULT NULL,
  `notes` varchar(500) DEFAULT NULL,
  `applied_to_inventory` tinyint(1) NOT NULL,
  `client_reference` varchar(64) DEFAULT NULL,
  `recommendation_item_id` int(11) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_purchase_client_reference` (`household_id`,`client_reference`),
  UNIQUE KEY `recommendation_item_id` (`recommendation_item_id`),
  KEY `ix_purchases_household_date` (`household_id`,`purchase_date`),
  KEY `ix_purchases_item_id` (`item_id`),
  CONSTRAINT `purchases_ibfk_1` FOREIGN KEY (`household_id`) REFERENCES `households` (`id`) ON DELETE CASCADE,
  CONSTRAINT `purchases_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `grocery_items` (`id`),
  CONSTRAINT `purchases_ibfk_3` FOREIGN KEY (`recommendation_item_id`) REFERENCES `recommendation_items` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS `consumption` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `household_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `quantity` decimal(12,3) NOT NULL,
  `consumed_at` date NOT NULL,
  `notes` varchar(500) DEFAULT NULL,
  `deducted_from_stock` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `item_id` (`item_id`),
  KEY `ix_consumption_household_item_date` (`household_id`,`item_id`,`consumed_at`),
  CONSTRAINT `consumption_ibfk_1` FOREIGN KEY (`household_id`) REFERENCES `households` (`id`) ON DELETE CASCADE,
  CONSTRAINT `consumption_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `grocery_items` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS `feedback` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `household_id` int(11) NOT NULL,
  `rating` int(11) NOT NULL,
  `comment` varchar(1000) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_feedback_household_id` (`household_id`),
  CONSTRAINT `feedback_ibfk_1` FOREIGN KEY (`household_id`) REFERENCES `households` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ck_feedback_rating_range` CHECK (`rating` between 1 and 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
