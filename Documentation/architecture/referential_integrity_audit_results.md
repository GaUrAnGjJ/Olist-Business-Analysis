# Table Grain, Relationship Map & Referential Integrity Audit

## Overview
This document outlines the entity definitions, table grain, entity relationship map (ERD), and cross-table referential integrity audit results for all datasets in the Olist project.

---

## 1. Table Grain & Relationship Map

| Dataset | Primary Key / Grain | Entity Description | Foreign Keys | Relationship / Cardinality |
| :--- | :--- | :--- | :--- | :--- |
| **`orders`** | `order_id` | One row per customer order | `customer_id` &rarr; `customers.customer_id` | **1:1** with `customers`; **1:N** with `order_items` & `payments` |
| **`customers`** | `customer_id` | One row per order-customer location key | None (Parent table) | **1:1** with `orders`; `customer_unique_id` identifies repeating customers |
| **`order_items`** | `(order_id, order_item_id)` | One row per item line in an order | `order_id` &rarr; `orders.order_id`<br>`product_id` &rarr; `products.product_id`<br>`seller_id` &rarr; `sellers.seller_id` | **N:1** with `orders`; **N:1** with `products` |
| **`payments`** | `(order_id, payment_sequential)` | One row per payment transaction installment/method | `order_id` &rarr; `orders.order_id` | **N:1** with `orders` |
| **`products`** | `product_id` | One row per unique product SKU | `product_category_name` &rarr; `category_translation.product_category_name` | **1:N** with `order_items`; **N:1** with `category_translation` |
| **`reviews`** | `review_id` (or `review_id, order_id`) | One row per customer survey response | `order_id` &rarr; `orders.order_id` | **N:1** with `orders` (multiple review entries per order possible) |
| **`category_translation`** | `product_category_name` | One row per Portuguese-to-English translation | None (Parent lookup table) | **1:N** with `products` |

---

## 2. Cross-Table Referential Integrity Audit

### A. Foreign Key Integrity (Child FK &rarr; Parent PK)

| Child Table | FK Column | Parent Table | PK Column | Total Non-Null FKs | Orphan Count | Integrity Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`orders`** | `customer_id` | `customers` | `customer_id` | 99,441 | 0 | **PASS (100% Valid)** |
| **`order_items`** | `order_id` | `orders` | `order_id` | 112,650 | 0 | **PASS (100% Valid)** |
| **`order_items`** | `product_id` | `products` | `product_id` | 112,650 | 0 | **PASS (100% Valid)** |
| **`payments`** | `order_id` | `orders` | `order_id` | 103,886 | 0 | **PASS (100% Valid)** |
| **`reviews`** | `order_id` | `orders` | `order_id` | 99,224 | 0 | **PASS (100% Valid)** |
| **`products`** | `product_category_name` | `category_translation` | `product_category_name` | 32,341 | **13** (0.04%) | **WARNING (13 Orphans)** |

> **Key Finding on `products` &rarr; `category_translation`**:
> 2 category names in `products` are missing from `category_translation`:
> 1. `'pc_gamer'`
> 2. `'portateis_cozinha_e_preparadores_de_alimentos'`
> 
> Together these 2 categories account for 13 product records in `products`.

---

### B. Reverse Parent Completeness (Parent PK &rarr; Child FK Existence)

- **`orders` without `order_items`**: **775** orders (0.78% of orders)
  - **603** `unavailable` orders
  - **164** `canceled` orders
  - **5** `created` orders
  - **2** `invoiced` orders
  - **1** `shipped` order
- **`orders` without `payments`**: **1** order (0.00%)
  - Order ID: `bfbd0f9bdef84302105ad712db648a6c` (Status: `delivered`). This represents a data anomaly where payment record is missing.
- **`orders` without `reviews`**: **768** orders (0.77% of orders)
- **`customers` without `orders`**: **0** customers (100% of customer records map to an order).

---

## 3. Summary & Next Steps
- Reusable functions `display_table_grain_and_relationships()` and `check_referential_integrity(datasets)` have been added to `src/Notebooks/data_quality_checks.py`.
- Integrated and executed as part of `src/Notebooks/audit.py`.
- Foreign key integrity across major core business entities (`orders`, `order_items`, `customers`, `payments`, `reviews`) is **100% valid**.
