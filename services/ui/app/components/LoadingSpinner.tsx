
export default function LoadingSpinner (){

    return (
        <div className="min-h-screen flex items-center justify-center">
        <div className="modern-card p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <div className="text-xl text-gray-700">Loading...</div>
        </div>
        </div>
    )
}