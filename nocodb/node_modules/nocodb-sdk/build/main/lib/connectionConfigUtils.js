"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.validateAndExtractSSLProp = void 0;
const enums_1 = require("../lib/enums");
const validateAndExtractSSLProp = (connectionConfig, sslUse, client) => {
    if ('ssl' in connectionConfig && connectionConfig.ssl) {
        if (sslUse === enums_1.SSLUsage.No ||
            (typeof connectionConfig.ssl === 'object' &&
                Object.values(connectionConfig.ssl).every((v) => v === null || v === undefined))) {
            return undefined;
        }
        // if postgres then only allow boolean or object
        else if (client === 'pg' &&
            ['true', 'false'].includes(connectionConfig.ssl)) {
            return connectionConfig.ssl === 'true';
        }
        else if (client === 'pg' &&
            !['boolean', 'object'].includes(typeof connectionConfig.ssl)) {
            return undefined;
        }
        return connectionConfig.ssl;
    }
};
exports.validateAndExtractSSLProp = validateAndExtractSSLProp;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiY29ubmVjdGlvbkNvbmZpZ1V0aWxzLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vc3JjL2xpYi9jb25uZWN0aW9uQ29uZmlnVXRpbHMudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6Ijs7O0FBQUEsdUNBQXVDO0FBRWhDLE1BQU0seUJBQXlCLEdBQUcsQ0FDdkMsZ0JBQXFCLEVBQ3JCLE1BQWdCLEVBQ2hCLE1BQWMsRUFDZCxFQUFFO0lBQ0YsSUFBSSxLQUFLLElBQUksZ0JBQWdCLElBQUksZ0JBQWdCLENBQUMsR0FBRyxFQUFFLENBQUM7UUFDdEQsSUFDRSxNQUFNLEtBQUssZ0JBQVEsQ0FBQyxFQUFFO1lBQ3RCLENBQUMsT0FBTyxnQkFBZ0IsQ0FBQyxHQUFHLEtBQUssUUFBUTtnQkFDdkMsTUFBTSxDQUFDLE1BQU0sQ0FBQyxnQkFBZ0IsQ0FBQyxHQUFHLENBQUMsQ0FBQyxLQUFLLENBQ3ZDLENBQUMsQ0FBQyxFQUFFLEVBQUUsQ0FBQyxDQUFDLEtBQUssSUFBSSxJQUFJLENBQUMsS0FBSyxTQUFTLENBQ3JDLENBQUMsRUFDSixDQUFDO1lBQ0QsT0FBTyxTQUFTLENBQUM7UUFDbkIsQ0FBQztRQUNELGdEQUFnRDthQUMzQyxJQUNILE1BQU0sS0FBSyxJQUFJO1lBQ2YsQ0FBQyxNQUFNLEVBQUUsT0FBTyxDQUFDLENBQUMsUUFBUSxDQUFDLGdCQUFnQixDQUFDLEdBQUcsQ0FBQyxFQUNoRCxDQUFDO1lBQ0QsT0FBTyxnQkFBZ0IsQ0FBQyxHQUFHLEtBQUssTUFBTSxDQUFDO1FBQ3pDLENBQUM7YUFBTSxJQUNMLE1BQU0sS0FBSyxJQUFJO1lBQ2YsQ0FBQyxDQUFDLFNBQVMsRUFBRSxRQUFRLENBQUMsQ0FBQyxRQUFRLENBQUMsT0FBTyxnQkFBZ0IsQ0FBQyxHQUFHLENBQUMsRUFDNUQsQ0FBQztZQUNELE9BQU8sU0FBUyxDQUFDO1FBQ25CLENBQUM7UUFFRCxPQUFPLGdCQUFnQixDQUFDLEdBQUcsQ0FBQztJQUM5QixDQUFDO0FBQ0gsQ0FBQyxDQUFDO0FBOUJXLFFBQUEseUJBQXlCLDZCQThCcEMifQ==