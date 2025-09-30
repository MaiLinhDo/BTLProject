import pyodbc
from app.config import Config

def get_connection():
    """Returns a connection to the SQL server."""
    return pyodbc.connect(Config.SQL_SERVER_CONN)

# Fetch a voucher by its code
def get_voucher_by_code(code):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Voucher WHERE Code = ?", (code,))
    voucher = cursor.fetchone()
    conn.close()
    return voucher

# Increment usage of a voucher
def update_voucher_usage(code):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Voucher SET SoLuongSuDung = SoLuongSuDung + 1 WHERE Code = ?", (code,))
    conn.commit()
    conn.close()
    return True

def get_vouchers(page, page_size, search_term):
    conn = get_connection()
    cursor = conn.cursor()
    offset = (page - 1) * page_size
    search_query = f"%{search_term}%"
    
    # Fetch the vouchers with search and pagination
    cursor.execute("""
        SELECT * FROM Voucher 
        WHERE Code LIKE ? OR MoTa LIKE ?
        ORDER BY NgayBatDau
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """, (search_query, search_query, offset, page_size))
    
    vouchers = cursor.fetchall()

    # Convert Row objects to dictionaries
    vouchers_list = []
    columns = [column[0] for column in cursor.description]  # Get column names
    
    for voucher in vouchers:
        voucher_dict = dict(zip(columns, voucher))
        vouchers_list.append(voucher_dict)

    # Get the total number of vouchers matching the search term
    cursor.execute("""
        SELECT COUNT(*) FROM Voucher
        WHERE Code LIKE ? OR MoTa LIKE ?
    """, (search_query, search_query))
    total = cursor.fetchone()[0]
    
    conn.close()
    
    return vouchers_list, total


# Create a new voucher
def create_voucher(data):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO Voucher (Code, GiamGia, NgayBatDau, NgayKetThuc, SoLuongSuDungToiDa, MoTa)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data.get('Code'), data.get('GiamGia'), data.get('NgayBatDau'),
              data.get('NgayKetThuc'), data.get('SoLuongSuDungToiDa'), data.get('MoTa')))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating voucher: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_voucher_by_id(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Voucher WHERE MaVoucher = ?", (id,))
    voucher = cursor.fetchone()
    
    if voucher:
        # Get column names
        columns = [column[0] for column in cursor.description]
        # Convert Row object to dictionary
        voucher_dict = dict(zip(columns, voucher))
    else:
        voucher_dict = None
    
    conn.close()
    
    return voucher_dict


# Update a voucher
def update_voucher_admin(id, data):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE Voucher 
            SET Code = ?, GiamGia = ?, NgayBatDau = ?, NgayKetThuc = ?, 
                SoLuongSuDungToiDa = ?, MoTa = ?
            WHERE MaVoucher = ?
        """, (data.get('Code'), data.get('GiamGia'), data.get('NgayBatDau'),
              data.get('NgayKetThuc'), data.get('SoLuongSuDungToiDa'), data.get('MoTa'), id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating voucher: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


# Toggle the status of the voucher (activate/deactivate)
def toggle_voucher_status(id):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE Voucher
            SET TrangThai = CASE 
                                WHEN TrangThai = 1 THEN 0
                                ELSE 1
                            END
            WHERE MaVoucher = ?
        """, (id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error toggling voucher status: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
