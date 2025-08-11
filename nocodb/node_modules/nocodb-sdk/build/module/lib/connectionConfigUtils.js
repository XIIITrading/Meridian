import { SSLUsage } from '../lib/enums';
export const validateAndExtractSSLProp = (connectionConfig, sslUse, client) => {
    if ('ssl' in connectionConfig && connectionConfig.ssl) {
        if (sslUse === SSLUsage.No ||
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
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiY29ubmVjdGlvbkNvbmZpZ1V0aWxzLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vc3JjL2xpYi9jb25uZWN0aW9uQ29uZmlnVXRpbHMudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUEsT0FBTyxFQUFFLFFBQVEsRUFBRSxNQUFNLGFBQWEsQ0FBQztBQUV2QyxNQUFNLENBQUMsTUFBTSx5QkFBeUIsR0FBRyxDQUN2QyxnQkFBcUIsRUFDckIsTUFBZ0IsRUFDaEIsTUFBYyxFQUNkLEVBQUU7SUFDRixJQUFJLEtBQUssSUFBSSxnQkFBZ0IsSUFBSSxnQkFBZ0IsQ0FBQyxHQUFHLEVBQUUsQ0FBQztRQUN0RCxJQUNFLE1BQU0sS0FBSyxRQUFRLENBQUMsRUFBRTtZQUN0QixDQUFDLE9BQU8sZ0JBQWdCLENBQUMsR0FBRyxLQUFLLFFBQVE7Z0JBQ3ZDLE1BQU0sQ0FBQyxNQUFNLENBQUMsZ0JBQWdCLENBQUMsR0FBRyxDQUFDLENBQUMsS0FBSyxDQUN2QyxDQUFDLENBQUMsRUFBRSxFQUFFLENBQUMsQ0FBQyxLQUFLLElBQUksSUFBSSxDQUFDLEtBQUssU0FBUyxDQUNyQyxDQUFDLEVBQ0osQ0FBQztZQUNELE9BQU8sU0FBUyxDQUFDO1FBQ25CLENBQUM7UUFDRCxnREFBZ0Q7YUFDM0MsSUFDSCxNQUFNLEtBQUssSUFBSTtZQUNmLENBQUMsTUFBTSxFQUFFLE9BQU8sQ0FBQyxDQUFDLFFBQVEsQ0FBQyxnQkFBZ0IsQ0FBQyxHQUFHLENBQUMsRUFDaEQsQ0FBQztZQUNELE9BQU8sZ0JBQWdCLENBQUMsR0FBRyxLQUFLLE1BQU0sQ0FBQztRQUN6QyxDQUFDO2FBQU0sSUFDTCxNQUFNLEtBQUssSUFBSTtZQUNmLENBQUMsQ0FBQyxTQUFTLEVBQUUsUUFBUSxDQUFDLENBQUMsUUFBUSxDQUFDLE9BQU8sZ0JBQWdCLENBQUMsR0FBRyxDQUFDLEVBQzVELENBQUM7WUFDRCxPQUFPLFNBQVMsQ0FBQztRQUNuQixDQUFDO1FBRUQsT0FBTyxnQkFBZ0IsQ0FBQyxHQUFHLENBQUM7SUFDOUIsQ0FBQztBQUNILENBQUMsQ0FBQyJ9