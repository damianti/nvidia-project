

function getRequiredEnv(key: string): string {
    const value = process.env[key]
    if (!value){
        throw new Error("Missing required environment variables")
    }
    return value
}

function getEnv(key: string, defaultValue: string): string{
    return process.env[key] || defaultValue
}

export const config = {

    apiGatewayUrl: getEnv("API_GATEWAY_EXTERNAL_URL", "http://localhost:8080"),

    validate(){
        try{
            new URL(this.apiGatewayUrl)
        }
        catch {
            throw new Error(`Invalid API_GATEWAY_EXTERNAL_URL: ${this.apiGatewayUrl}`)
        }
    }
}
config.validate()
