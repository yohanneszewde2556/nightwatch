import React from 'react';

export interface TableProps extends React.TableHTMLAttributes<HTMLTableElement> {
  children: React.ReactNode;
}

export const Table: React.FC<TableProps> = ({ children, className = '', style, ...props }) => {
  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <table
        className={`nw-table ${className}`}
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: 'var(--font-size-13)',
          textAlign: 'left',
          ...style,
        }}
        {...props}
      >
        {children}
      </table>
    </div>
  );
};

export const TableHead: React.FC<React.HTMLAttributes<HTMLTableSectionElement>> = ({
  children,
  style,
  ...props
}) => {
  return (
    <thead
      style={{
        borderBottom: '1px solid var(--border-subtle)',
        color: 'var(--text-muted)',
        fontSize: 'var(--font-size-12)',
        fontWeight: 500,
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
        ...style,
      }}
      {...props}
    >
      {children}
    </thead>
  );
};

export const TableRow: React.FC<React.HTMLAttributes<HTMLTableRowElement> & { hoverable?: boolean }> = ({
  children,
  hoverable = true,
  style,
  className = '',
  ...props
}) => {
  return (
    <tr
      className={`nw-table-row ${hoverable ? 'nw-table-row-hoverable' : ''} ${className}`}
      style={{
        borderBottom: '1px solid var(--border-subtle)',
        transition: 'background-color var(--motion-fast)',
        ...style,
      }}
      {...props}
    >
      {children}
    </tr>
  );
};

export const TableHeaderCell: React.FC<React.ThHTMLAttributes<HTMLTableCellElement>> = ({
  children,
  style,
  ...props
}) => {
  return (
    <th
      style={{
        padding: '10px 14px',
        fontWeight: 500,
        ...style,
      }}
      {...props}
    >
      {children}
    </th>
  );
};

export const TableCell: React.FC<React.TdHTMLAttributes<HTMLTableCellElement>> = ({
  children,
  style,
  ...props
}) => {
  return (
    <td
      style={{
        padding: '12px 14px',
        color: 'var(--text-primary)',
        verticalAlign: 'middle',
        ...style,
      }}
      {...props}
    >
      {children}
    </td>
  );
};
