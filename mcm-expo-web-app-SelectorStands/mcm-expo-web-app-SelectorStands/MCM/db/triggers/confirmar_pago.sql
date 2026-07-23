-- Al marcar una factura como pagada en su totalidad, bloquea el stand y
-- formaliza la reserva asociada. Requiere schema.sql ya aplicado.

CREATE OR REPLACE FUNCTION fn_confirmar_bloqueo_stand()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.estado_factura = 'Pagada_Total' THEN
        UPDATE stand
        SET estado_stand = 'Bloqueado'
        FROM reserva, contrato
        WHERE contrato.id_contrato = NEW.id_contrato
          AND reserva.id_reserva = contrato.id_reserva
          AND stand.id_stand = reserva.id_stand;

        UPDATE reserva
        SET estado_reserva = 'Formalizada'
        FROM contrato
        WHERE contrato.id_contrato = NEW.id_contrato
          AND reserva.id_reserva = contrato.id_reserva;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_confirmar_pago_stand
AFTER UPDATE OF estado_factura ON factura
FOR EACH ROW
EXECUTE FUNCTION fn_confirmar_bloqueo_stand();
