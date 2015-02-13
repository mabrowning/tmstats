function Welford( init )
{
    if( init == undefined )
    {
        this.n  = 0;
        this.M1 = 0;
        this.M2 = 0;
        this.M3 = 0;
        this.M4 = 0;
    }
    else if( typeof(init) == "number" )
    {
        this.n = 1;
        this.M1 = init/10;
        this.M2 = 0;
        this.M3 = 0;
        this.M4 = 0;
    }
    else
    {
        this.n = init[0];
        this.M1 = init[1]/10;
        this.M2 = init[2]/10;
        this.M3 = init[3]/10;
        this.M4 = init[4]/10;
    }

}

Welford.prototype.combine = function(b)
{
    a = this;
    c = new Welford()
    c.n = a.n + b.n
    delta  = b.M1 - a.M1
    delta2 = delta  * delta
    delta3 = delta2 * delta
    delta4 = delta2 * delta2

    c.M1 = ( a.n * a.M1 + b.n * b.M1 ) / c.n
    c.M2 = a.M2 + b.M2 + delta2 * a.n * b.n / c.n
    c.M3 = a.M3 + b.M3 + delta3 * a.n * b.n * (a.n - b.n)/(c.n*c.n) + 
                3.0*delta * (a.n*b.M2 - b.n*a.M2) / c.n;
    c.M4 = a.M4 + b.M4 + delta4*a.n*b.n * (a.n*a.n - a.n*b.n + b.n*b.n) / (c.n*c.n*c.n) + 
                6.0*delta2 * (a.n*a.n*b.M2 + b.n*b.n*a.M2)/(c.n*c.n) + 4.0*delta*(a.n*b.M3 - b.n*a.M3) / c.n;

    return c
}

Welford.prototype.mean = function()
{
    return this.M1;
}

Welford.prototype.meanstd = function()
{
    return this.std() / Math.sqrt( this.n );
}

Welford.prototype.variance = function()
{
    return this.M2/(this.n-1);
}

Welford.prototype.std = function()
{
    return Math.sqrt(this.variance())
}

Welford.prototype.skewness = function()
{
    return Math.sqrt( this.n ) * this.M3 / ( this.M2 * Math.sqrt( this.M2 ) )
}

Welford.prototype.kurtosis = function()
{
    return this.n * this.M4 / (this.M2 * this.M2 ) - 3
}
