-- Patrón de referencia para guardar_reserva() (ver pages/cliente_selector.py).
-- El SELECT ... FOR UPDATE evita que dos clientes reserven el mismo stand
-- al mismo tiempo (race condition): la segunda transacción concurrente queda
-- bloqueada hasta que la primera hace COMMIT/ROLLBACK, y entonces relee un
-- estado_stand ya actualizado.

BEGIN TRANSACTION;

-- 1. Bloqueo pesimista sobre el stand que el cliente quiere reservar.
SELECT estado_stand
FROM stand
WHERE id_stand = :id_stand FOR UPDATE;

-- 2. Verificar que siga disponible y actualizar estado.
UPDATE stand
SET estado_stand = 'Pre_Reservado'
WHERE id_stand = :id_stand AND estado_stand = 'Disponible';

-- Si la fila anterior actualizó 0 registros, el stand ya no estaba
-- disponible: se debe hacer ROLLBACK y devolver un error al cliente.

-- 3. Insertar la reserva.
INSERT INTO reserva (id_stand, id_marca, estado_reserva)
VALUES (:id_stand, :id_marca, 'Pendiente');

COMMIT;
