This stock picking algorithm was in effect for myself and a friend (with a fairly small amount of cash) from April 2017 to September 2018, at which point a regulatory side effect of my new employement made it difficult to continue without disproportionate pain.  We ran the algorithm quarterly via Quantopian, examined the output, and made corresponding stock picks on Robinhood.  In our first (really only) year, we beat the S&P 500, which was a fun feeling.  

It's based on strategies outlined in Patrick O'Shaughnessy's __Millenial Money: How Young Investors Can Build a Fortune__.  

## Building ##

The source for the algorithm lives in src/algo.  It can be built by running `python scripts/construct.py` which will generate a file `stage/construction/algo.py`.  This file can be dropped in as a Quantopian algorithm.

## Disclaimer ##

I am not a financial advisor, and this repository should not be construed as financial advice.  Furthermore:

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
