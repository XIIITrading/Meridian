declare enum AuditOperationTypes {
    COMMENT = "COMMENT",
    DATA = "DATA",
    PROJECT = "PROJECT",
    VIRTUAL_RELATION = "VIRTUAL_RELATION",
    RELATION = "RELATION",
    TABLE_VIEW = "TABLE_VIEW",
    TABLE = "TABLE",
    VIEW = "VIEW",
    META = "META",
    TABLE_COLUMN = "TABLE_COLUMN",
    WEBHOOKS = "WEBHOOKS",
    AUTHENTICATION = "AUTHENTICATION",
    ORG_USER = "ORG_USER"
}
declare enum AuditOperationSubTypes {
    INSERT = "INSERT",
    CREATE = "CREATE",
    UPDATE = "UPDATE",
    DELETE = "DELETE",
    BULK_INSERT = "BULK_INSERT",
    BULK_UPDATE = "BULK_UPDATE",
    BULK_DELETE = "BULK_DELETE",
    LINK_RECORD = "LINK_RECORD",
    UNLINK_RECORD = "UNLINK_RECORD",
    RENAME = "RENAME",
    IMPORT_FROM_ZIP = "IMPORT_FROM_ZIP",
    EXPORT_TO_FS = "EXPORT_TO_FS",
    EXPORT_TO_ZIP = "EXPORT_TO_ZIP",
    SIGNIN = "SIGNIN",
    SIGNUP = "SIGNUP",
    PASSWORD_RESET = "PASSWORD_RESET",
    PASSWORD_FORGOT = "PASSWORD_FORGOT",
    PASSWORD_CHANGE = "PASSWORD_CHANGE",
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION",
    ROLES_MANAGEMENT = "ROLES_MANAGEMENT",
    INVITE = "INVITE",
    RESEND_INVITE = "RESEND_INVITE"
}
declare const auditOperationTypeLabels: {
    COMMENT: string;
    DATA: string;
    PROJECT: string;
    VIRTUAL_RELATION: string;
    RELATION: string;
    TABLE_VIEW: string;
    TABLE: string;
    VIEW: string;
    META: string;
    WEBHOOKS: string;
    AUTHENTICATION: string;
    TABLE_COLUMN: string;
    ORG_USER: string;
};
declare const auditOperationSubTypeLabels: {
    UPDATE: string;
    INSERT: string;
    DELETE: string;
    BULK_INSERT: string;
    BULK_UPDATE: string;
    BULK_DELETE: string;
    LINK_RECORD: string;
    UNLINK_RECORD: string;
    CREATE: string;
    RENAME: string;
    IMPORT_FROM_ZIP: string;
    EXPORT_TO_FS: string;
    EXPORT_TO_ZIP: string;
    SIGNIN: string;
    SIGNUP: string;
    PASSWORD_RESET: string;
    PASSWORD_FORGOT: string;
    PASSWORD_CHANGE: string;
    EMAIL_VERIFICATION: string;
    ROLES_MANAGEMENT: string;
    INVITE: string;
    RESEND_INVITE: string;
};
interface AuditV0 {
    id: string;
    user: string;
    ip: string;
    fk_workspace_id: string | null;
    base_id: string | null;
    source_id: string | null;
    fk_model_id: string | null;
    row_id: string | null;
    op_type: AuditOperationTypes;
    op_sub_type: AuditOperationSubTypes;
    description: string | null;
    details: string | null;
    created_at: string;
    updated_at: string;
}
export { AuditV0, AuditOperationTypes, AuditOperationSubTypes, auditOperationTypeLabels, auditOperationSubTypeLabels, };
