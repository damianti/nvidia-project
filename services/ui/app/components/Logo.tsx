import Image from 'next/image'

export default function Logo(){
    return (
        <div className="flex items-center space-x-2">
            <Image
                src='/proyect-logo.png'
                alt="NVIDIA Cloud Logo"
                width={40}
                height={40}
            />
            <span className="text-xl font-bold"> NVIDIA Cloud</span>
        </div>
    )
}