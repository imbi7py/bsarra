local_old = "/home/daniel/Desktop/SP/"

local_new = "/home/daniel/Desktop/SP_novo/"
local_header = "/home/daniel/Desktop/SP_antigo/"

estacoes = list.files(path= "/home/daniel/Desktop/SP/", recursive = FALSE)

for(est in estacoes){
  file_old=paste(local_old,est,sep='')
  
  file_new = paste(local_new,est,sep='')
  
  file_header = paste(local_header,est,sep='')
  
  est = read.table(file_old, header = TRUE, sep = ",")
  
  est2 = read.table(file_header,sep="\t")

  estimada = "não"
  
  zero = 0
  
  df = data.frame(est$data,est$tMin,estimada,est$tMed,estimada,est$tMax,estimada,zero,estimada,zero,estimada,est$precipitacao,estimada)
  
  colnames(df) = c("data","tMin","tMin Estimada","tMed","tMed Estimada","tMax","tMax Estimada","urMin","urMin Estimada","urMax","urMax Estimada","precipitacao","precipitacao Estimada")

  
  header = paste(est2[1:5,1],sep="")
  
  header = paste(header,"\n",sep="")
  
  
  cat('',file=file_new)
  
  for(i in 1:5){
    
    cat(header[i],file=file_new,append=TRUE)
  }
  
  cat('\n',file=file_new,append=TRUE)
  
  write.table(df, file_new, append = T,quote=FALSE,sep=";",row.names = FALSE)
}