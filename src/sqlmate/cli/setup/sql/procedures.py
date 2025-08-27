CREATE_SAVE_USER_TABLE_PROC = """
CREATE PROCEDURE {db_name}.save_user_table (
	IN p_user_id INT,
	IN p_username VARCHAR(50),
	IN p_table_name VARCHAR(100),
	IN p_created_at DATETIME,
	IN p_query TEXT
)
BEGIN
	DECLARE full_table_name VARCHAR(150);
	
	SELECT COUNT(*) INTO @exists FROM sqlmate.user_tables WHERE user_id = p_user_id AND table_name = p_table_name;
	IF @exists > 0 THEN
	SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Table already exists';
	END IF;
	
	SET full_table_name = CONCAT('sqlmate.u_', p_username, '_', p_table_name);

	-- Prevent SQL injection
	IF full_table_name REGEXP '^[a-zA-Z0-9_.]+$' THEN
		-- Dynamically prepare the CREATE TABLE query
		SET @create_sql = CONCAT('CREATE TABLE ', full_table_name, ' AS ', p_query);
		PREPARE stmt FROM @create_sql;
		EXECUTE stmt;
		DEALLOCATE PREPARE stmt;

		-- Insert mapping into user_tables
		INSERT INTO sqlmate.user_tables (user_id, table_name, created_at) 
		VALUES (p_user_id, p_table_name, p_created_at);
	ELSE
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid table name format';
	END IF;
END
"""

CREATE_PROCESS_TABLE_TO_DROP_PROC = """
CREATE PROCEDURE sqlmate.process_tables_to_drop()
BEGIN
	DECLARE v_user_id INT;
    DECLARE v_table_name VARCHAR(100);
    DECLARE v_done INT DEFAULT FALSE;
    DECLARE v_sql VARCHAR(500);
    
    -- Cursor to iterate through tables_to_drop
    DECLARE cur CURSOR FOR 
        SELECT user_id, table_name FROM tables_to_drop LIMIT 100;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = TRUE;
    
    OPEN cur;
    
    REPEAT
        FETCH cur INTO v_user_id, v_table_name;
        
        IF NOT v_done THEN
            -- Get the username for this user_id
            SET @v_username = (SELECT username FROM sqlmate.users WHERE id = v_user_id LIMIT 1);
            
			-- Drop the table
			SET @sql = CONCAT('DROP TABLE IF EXISTS u_', @v_username, '_', v_table_name);
			PREPARE stmt FROM @sql;
			EXECUTE stmt;
			DEALLOCATE PREPARE stmt;
			
			-- Remove record from log table
			DELETE FROM tables_to_drop WHERE user_id = v_user_id AND table_name = v_table_name;
		END IF;
    UNTIL v_done
    END REPEAT;
    
    CLOSE cur;
END
"""